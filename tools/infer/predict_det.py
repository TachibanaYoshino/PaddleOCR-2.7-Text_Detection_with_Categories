# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, '../..')))

os.environ["FLAGS_allocator_strategy"] = 'auto_growth'

import cv2,random
import numpy as np
import time
import sys

import tools.infer.utility as utility
from ppocr.utils.logging import get_logger
from ppocr.utils.utility import get_image_file_list, check_and_read
from ppocr.data import create_operators, transform
from ppocr.postprocess import build_post_process
import json
logger = get_logger()

random.seed(1123)
def generate_color():
    r = random.randint(0, 255)  # 生成红色分量（范围为0-255）
    g = random.randint(0, 255)  # 生成绿色分量（范围为0-255）
    b = random.randint(0, 255)  # 生成蓝色分量（范围为0-255）
    return (r, g, b)

def draw_det_res_and_label(dt_boxes, classes, labels, img,colors):
    if len(dt_boxes) > 0:
        import cv2
        index = 0
        src_im = img
        for box in dt_boxes:
            box = box.astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(src_im, [box], True, color=colors[classes[index]], thickness=2)
            font = cv2.FONT_HERSHEY_SIMPLEX
            src_im = cv2.putText(src_im, labels[classes[index]], (box[0][0][0], box[0][0][1]), font, 0.5, colors[classes[index]], 1)
            index += 1
        return src_im
    else:
        return img


class TextDetector(object):
    def __init__(self, args):
        self.args = args
        self.det_algorithm = args.det_algorithm
        self.use_onnx = args.use_onnx
        pre_process_list = [{
            'DetResizeForTest': {
                'limit_side_len': args.det_limit_side_len,
                'limit_type': args.det_limit_type,
            }
        }, {
            'NormalizeImage': {
                'std': [0.229, 0.224, 0.225],
                'mean': [0.485, 0.456, 0.406],
                'scale': '1./255.',
                'order': 'hwc'
            }
        }, {
            'ToCHWImage': None
        }, {
            'KeepKeys': {
                'keep_keys': ['image', 'shape']
            }
        }]
        postprocess_params = {}
        if self.det_algorithm == "DB":
            postprocess_params['name'] = 'DBPostProcess'
            postprocess_params["thresh"] = args.det_db_thresh
            postprocess_params["box_thresh"] = args.det_db_box_thresh
            postprocess_params["max_candidates"] = 1000
            postprocess_params["unclip_ratio"] = args.det_db_unclip_ratio
            postprocess_params["use_dilation"] = args.use_dilation
            postprocess_params["score_mode"] = args.det_db_score_mode
            postprocess_params["box_type"] = args.det_box_type
        elif self.det_algorithm == "DB++":
            postprocess_params['name'] = 'DBPostProcess'
            postprocess_params["thresh"] = args.det_db_thresh
            postprocess_params["box_thresh"] = args.det_db_box_thresh
            postprocess_params["max_candidates"] = 1000
            postprocess_params["unclip_ratio"] = args.det_db_unclip_ratio
            postprocess_params["use_dilation"] = args.use_dilation
            postprocess_params["score_mode"] = args.det_db_score_mode
            postprocess_params["box_type"] = args.det_box_type
            pre_process_list[1] = {
                'NormalizeImage': {
                    'std': [1.0, 1.0, 1.0],
                    'mean':
                    [0.48109378172549, 0.45752457890196, 0.40787054090196],
                    'scale': '1./255.',
                    'order': 'hwc'
                }
            }
        elif self.det_algorithm == "EAST":
            postprocess_params['name'] = 'EASTPostProcess'
            postprocess_params["score_thresh"] = args.det_east_score_thresh
            postprocess_params["cover_thresh"] = args.det_east_cover_thresh
            postprocess_params["nms_thresh"] = args.det_east_nms_thresh
        elif self.det_algorithm == "SAST":
            pre_process_list[0] = {
                'DetResizeForTest': {
                    'resize_long': args.det_limit_side_len
                }
            }
            postprocess_params['name'] = 'SASTPostProcess'
            postprocess_params["score_thresh"] = args.det_sast_score_thresh
            postprocess_params["nms_thresh"] = args.det_sast_nms_thresh

            if args.det_box_type == 'poly':
                postprocess_params["sample_pts_num"] = 6
                postprocess_params["expand_scale"] = 1.2
                postprocess_params["shrink_ratio_of_width"] = 0.2
            else:
                postprocess_params["sample_pts_num"] = 2
                postprocess_params["expand_scale"] = 1.0
                postprocess_params["shrink_ratio_of_width"] = 0.3

        elif self.det_algorithm == "PSE":
            postprocess_params['name'] = 'PSEPostProcess'
            postprocess_params["thresh"] = args.det_pse_thresh
            postprocess_params["box_thresh"] = args.det_pse_box_thresh
            postprocess_params["min_area"] = args.det_pse_min_area
            postprocess_params["box_type"] = args.det_box_type
            postprocess_params["scale"] = args.det_pse_scale
        elif self.det_algorithm == "FCE":
            pre_process_list[0] = {
                'DetResizeForTest': {
                    'rescale_img': [1080, 736]
                }
            }
            postprocess_params['name'] = 'FCEPostProcess'
            postprocess_params["scales"] = args.scales
            postprocess_params["alpha"] = args.alpha
            postprocess_params["beta"] = args.beta
            postprocess_params["fourier_degree"] = args.fourier_degree
            postprocess_params["box_type"] = args.det_box_type
        elif self.det_algorithm == "CT":
            pre_process_list[0] = {'ScaleAlignedShort': {'short_size': 640}}
            postprocess_params['name'] = 'CTPostProcess'
        else:
            logger.info("unknown det_algorithm:{}".format(self.det_algorithm))
            sys.exit(0)

        self.preprocess_op = create_operators(pre_process_list)
        self.postprocess_op = build_post_process(postprocess_params)
        self.predictor, self.input_tensor, self.output_tensors, self.config = utility.create_predictor(
            args, 'det', logger)

        if self.use_onnx:
            img_h, img_w = self.input_tensor.shape[2:]
            if isinstance(img_h, str) or isinstance(img_w, str):
                pass
            elif img_h is not None and img_w is not None and img_h > 0 and img_w > 0:
                pre_process_list[0] = {
                    'DetResizeForTest': {
                        'image_shape': [img_h, img_w]
                    }
                }
        self.preprocess_op = create_operators(pre_process_list)

        if args.benchmark:
            import auto_log
            pid = os.getpid()
            gpu_id = utility.get_infer_gpuid()
            self.autolog = auto_log.AutoLogger(
                model_name="det",
                model_precision=args.precision,
                batch_size=1,
                data_shape="dynamic",
                save_path=None,
                inference_config=self.config,
                pids=pid,
                process_name=None,
                gpu_ids=gpu_id if args.use_gpu else None,
                time_keys=[
                    'preprocess_time', 'inference_time', 'postprocess_time'
                ],
                warmup=2,
                logger=logger)

    def order_points_clockwise(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        tmp = np.delete(pts, (np.argmin(s), np.argmax(s)), axis=0)
        diff = np.diff(np.array(tmp), axis=1)
        rect[1] = tmp[np.argmin(diff)]
        rect[3] = tmp[np.argmax(diff)]
        return rect

    def clip_det_res(self, points, img_height, img_width):
        for pno in range(points.shape[0]):
            points[pno, 0] = int(min(max(points[pno, 0], 0), img_width - 1))
            points[pno, 1] = int(min(max(points[pno, 1], 0), img_height - 1))
        return points

    def filter_tag_det_res(self, dt_boxes, image_shape):
        img_height, img_width = image_shape[0:2]
        dt_boxes_new = []
        for box in dt_boxes:
            if type(box) is list:
                box = np.array(box)
            box = self.order_points_clockwise(box)
            box = self.clip_det_res(box, img_height, img_width)
            rect_width = int(np.linalg.norm(box[0] - box[1]))
            rect_height = int(np.linalg.norm(box[0] - box[3]))
            if rect_width <= 3 or rect_height <= 3:
                continue
            dt_boxes_new.append(box)
        dt_boxes = np.array(dt_boxes_new)
        return dt_boxes

    def filter_tag_det_res_and_label(self, dt_boxes, dt_labels, dt_label_scores, image_shape):
        img_height, img_width = image_shape[0:2]
        dt_boxes_new = []
        dt_labels_new = []
        dt_label_scores_new = []
        index = 0
        for box in dt_boxes:
            index += 1
            box = self.order_points_clockwise(box)
            box = self.clip_det_res(box, img_height, img_width)
            rect_width = int(np.linalg.norm(box[0] - box[1]))
            rect_height = int(np.linalg.norm(box[0] - box[3]))
            if rect_width <= 3 or rect_height <= 3:
                continue
            box = box-20 # Corresponding to padding post-processing
            dt_boxes_new.append(box)
            dt_labels_new.append(dt_labels[index - 1])
            dt_label_scores_new.append(dt_label_scores[index - 1])
        dt_boxes = np.array(dt_boxes_new)
        return dt_boxes, dt_labels_new, dt_label_scores_new

    def filter_tag_det_res_only_clip(self, dt_boxes, image_shape):
        img_height, img_width = image_shape[0:2]
        dt_boxes_new = []
        for box in dt_boxes:
            if type(box) is list:
                box = np.array(box)
            box = self.clip_det_res(box, img_height, img_width)
            dt_boxes_new.append(box)
        dt_boxes = np.array(dt_boxes_new)
        return dt_boxes

    def __call__(self, img, cls=True):

        # Padding preprocessing edge
        h,w = img.shape[:2]
        temp = np.zeros((h+20, w+20, img.shape[2]),img.dtype) +255
        temp[20:,20:] = img
        img = temp
        # img = np.concatenate([np.ones((20, w, img.shape[2]),img.dtype) +255, img], axis=0)
        # img = np.concatenate([np.ones((h, 20, img.shape[2]),img.dtype) +255, img], axis=1)
        ##
        ori_im = img.copy()
        data = {'image': img}

        st = time.time()

        if self.args.benchmark:
            self.autolog.times.start()

        data = transform(data, self.preprocess_op)
        img, shape_list = data
        # print(shape_list)
        if img is None:
            return None, 0
        img = np.expand_dims(img, axis=0)
        shape_list = np.expand_dims(shape_list, axis=0)
        img = img.copy()

        if self.args.benchmark:
            self.autolog.times.stamp()
        if self.use_onnx:
            input_dict = {}
            input_dict[self.input_tensor.name] = img
            outputs = self.predictor.run(self.output_tensors, input_dict)
        else:
            self.input_tensor.copy_from_cpu(img)
            self.predictor.run()
            outputs = []
            for output_tensor in self.output_tensors:
                output = output_tensor.copy_to_cpu()
                outputs.append(output)
            if self.args.benchmark:
                self.autolog.times.stamp()

        preds = {}
        if self.det_algorithm == "EAST":
            preds['f_geo'] = outputs[0]
            preds['f_score'] = outputs[1]
        elif self.det_algorithm == 'SAST':
            preds['f_border'] = outputs[0]
            preds['f_score'] = outputs[1]
            preds['f_tco'] = outputs[2]
            preds['f_tvo'] = outputs[3]
        elif self.det_algorithm in ['DB', 'PSE', 'DB++']:
            if cls:
                preds['classes'] = outputs[0]
                preds['maps'] = outputs[1]
            else:
                preds['maps'] = outputs[0]
        elif self.det_algorithm == 'FCE':
            for i, output in enumerate(outputs):
                preds['level_{}'.format(i)] = output
        elif self.det_algorithm == "CT":
            preds['maps'] = outputs[0]
            preds['score'] = outputs[1]
        else:
            raise NotImplementedError

        post_result = self.postprocess_op(preds, shape_list)
        dt_boxes = post_result[0]['points']

        if self.args.det_box_type == 'poly':
            dt_boxes = self.filter_tag_det_res_only_clip(dt_boxes, ori_im.shape)
        else:
            if cls:
                dt_boxes, dt_labels, dt_label_scores = self.filter_tag_det_res_and_label(dt_boxes,
                                                                                         post_result[0]["classes"],
                                                                                         post_result[0]["class_scores"],
                                                                                         ori_im.shape)
            else:
                dt_boxes = self.filter_tag_det_res(dt_boxes, ori_im.shape)
        # else:
        #     dt_boxes = self.filter_tag_det_res(dt_boxes, ori_im.shape)

        if self.args.benchmark:
            self.autolog.times.end(stamp=True)
        et = time.time()
        if cls:
            return dt_boxes, dt_labels, dt_label_scores, et - st
        else:
            return dt_boxes, et - st


if __name__ == "__main__":
    args = utility.parse_args()
    image_file_list = get_image_file_list(args.image_dir)
    text_detector = TextDetector(args)
    total_time = 0
    draw_img_save_dir = args.draw_img_save_dir
    os.makedirs(draw_img_save_dir, exist_ok=True)

    class_list = "datasets/enjp/label_list.txt"
    labels = []
    if class_list is not None:
        if isinstance(class_list, str):
            with open(class_list, "r+", encoding="utf-8") as f:
                for line in f.readlines():
                    labels.append(line.replace("\n", ""))
        else:
            labels = class_list
    else:
        raise "label_list need to be defined."
    colors = {i: generate_color() for i in range(len(labels))}

    if args.warmup:
        img = np.random.uniform(0, 255, [640, 640, 3]).astype(np.uint8)
        for i in range(2):
            res = text_detector(img)

    save_results = []
    for idx, image_file in enumerate(image_file_list):
        img, flag_gif, flag_pdf = check_and_read(image_file)
        if not flag_gif and not flag_pdf:
            img = cv2.imread(image_file)
        if not flag_pdf:
            if img is None:
                logger.debug("error in loading image:{}".format(image_file))
                continue
            imgs = [img]
        else:
            page_num = args.page_num
            if page_num > len(img) or page_num == 0:
                page_num = len(img)
            imgs = img[:page_num]
        for index, img in enumerate(imgs):
            st = time.time()
            dt_boxes, dt_labels, dt_label_scores, cost = text_detector(img)
            elapse = time.time() - st
            total_time += elapse
            if len(imgs) > 1:
                save_pred = os.path.basename(image_file) + '_' + str(
                    index) + "\t" + str(
                        json.dumps([x.tolist() for x in dt_boxes])) + "\n"
            else:
                save_pred = os.path.basename(image_file) + "\t" + str(
                    json.dumps([x.tolist() for x in dt_boxes])) + "\n"
            save_results.append(save_pred)
            logger.info(save_pred)
            if len(imgs) > 1:
                logger.info("{}_{} The predict time of {}: {}".format(
                    idx, index, image_file, elapse))
            else:
                logger.info("{} The predict time of {}: {}".format(
                    idx, image_file, elapse))

            src_im = draw_det_res_and_label(dt_boxes, dt_labels, labels, img, colors)
            # src_im = utility.draw_text_det_res(dt_boxes, img)

            if flag_gif:
                save_file = image_file[:-3] + "png"
            elif flag_pdf:
                save_file = image_file.replace('.pdf',
                                               '_' + str(index) + '.png')
            else:
                save_file = image_file
            img_path = os.path.join(
                draw_img_save_dir,
                "det_res_{}".format(os.path.basename(save_file)))
            cv2.imwrite(img_path, src_im)
            logger.info("The visualized image saved in {}".format(img_path))

    with open(os.path.join(draw_img_save_dir, "det_results.txt"), 'w') as f:
        f.writelines(save_results)
        f.close()
    if args.benchmark:
        text_detector.autolog.report()
