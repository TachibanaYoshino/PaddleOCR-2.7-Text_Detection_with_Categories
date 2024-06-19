import os,sys,json,copy
__dir__ = os.path.dirname(os.path.abspath(__file__))

import numpy as np

sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, '..')))
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, '../ppocr/metrics')))

from eval_det_iou import DetectionIoUEvaluator

class DetMetric(object):
    def __init__(self, main_indicator='hmean', **kwargs):
        self.evaluator = DetectionIoUEvaluator()
        self.main_indicator = main_indicator
        self.reset()

    def __call__(self, preds, gts, **kwargs):
        '''
       batch: a list produced by dataloaders.
           image: np.ndarray  of shape (N, C, H, W).
           ratio_list: np.ndarray  of shape(N,2)
           polygons: np.ndarray  of shape (N, K, 4, 2), the polygons of objective regions.
           ignore_tags: np.ndarray  of shape (N, K), indicates whether a region is ignorable or not.
       preds: a list of dict produced by post process
            points: np.ndarray of shape (N, K, 4, 2), the polygons of objective regions.
       '''

        for pred, gt_polyons in zip(preds, gts):
            # prepare gt
            gt_info_list = [{
                'points': gt_polyon,
                'text': '',
                'ignore': False
            } for gt_polyon in gt_polyons]
            # prepare det
            det_info_list = [{
                'points': det_polyon,
                'text': ''
            } for det_polyon in pred['points']]
            result = self.evaluator.evaluate_image(gt_info_list, det_info_list)
            self.results.append(result)

    def get_metric(self):
        """
        return metrics {
                 'precision': 0,
                 'recall': 0,
                 'hmean': 0
            }
        """

        metrics = self.evaluator.combine_results(self.results)
        self.reset()
        return metrics

    def reset(self):
        self.results = []  # clear results



def get_eval_out(preds, gts):
    eval_class = DetMetric()
    eval_class(preds, gts)
    # Get final metric，eg. acc or hmean
    metric = eval_class.get_metric()
    for k, v in metric.items():
        print('{}:{}'.format(k, v))

if __name__ == '__main__':
    preds, gts = [], []
    pree = {}
    pred_path = "temp2_1" # JSON directory of testset labeling, labelme format
    gt_path = "../datasets/enjp/valid/val.txt" # Testset annotation txt file, PaddleOCR text detection data format
    # gt_path = "aa.txt"
    c =0
    with open(gt_path,'r') as read:
        for line in read.readlines():

            file, boxs = line.strip().split("\t")
            boxs = eval(boxs)
            boxs = [ x["points"] for x in boxs]
            boxs = np.array(boxs,dtype=np.int32)

            with open(os.path.join(pred_path, file.replace("images/","").rsplit(".")[0] + ".json"), "r") as f:
                json_data = json.load(f)
                """polygen"""
                # a= [info["points"] for info in json_data["shapes"] ]
                # pree["points"] = np.array(a,dtype=np.int32)
                """retangle"""
                a=[]
                for info in json_data["shapes"]:
                    temp_points = np.array(info["points"])
                    xmin, ymin = [int(x) for x in temp_points.min(axis=0)]
                    xmax, ymax = [int(x) for x in temp_points.max(axis=0)]
                    pps = [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]
                    a.append(pps)
                pree["points"] = np.array(a,dtype=np.int32)
            # break
            preds.append(copy.deepcopy(pree))
            gts.append(boxs)
            # print(preds)
            # print( gts)
            # print(c, file)
            c += 1
    get_eval_out(preds, gts)
    print(c)


