





# export FLAGS_set_to_1d=False && export CUDA_VISIBLE_DEVICES=3 && python3 tools/eval.py -c configs/ch_PP-OCRv3_det_student_pretrained_mb3.yml -o Global.checkpoints="checkpoints/enjp/ch_PP-OCR_MobileNetV3_det/best_accuracy"  PostProcess.box_thresh=0.5 PostProcess.unclip_ratio=1.5
#
#
# export FLAGS_set_to_1d=False && export CUDA_VISIBLE_DEVICES=3 && python3 tools/eval.py -c configs/ch_PP-OCRv2_det_pretrained_res18.yml -o Global.checkpoints="checkpoints/enjp/ch_PP-OCR_res18_det/best_accuracy"  PostProcess.box_thresh=0.5 PostProcess.unclip_ratio=1.5
#
# export FLAGS_set_to_1d=False && export CUDA_VISIBLE_DEVICES=3 && python3 tools/eval.py -c configs/ch_PP-OCRv4_det_PPHGNet_small.yml -o Global.checkpoints="checkpoints/enjp/ch_PP-OCR_PPHGNet_small_det/best_accuracy"  PostProcess.box_thresh=0.5 PostProcess.unclip_ratio=1.5


 export FLAGS_set_to_1d=False && export CUDA_VISIBLE_DEVICES=3 && python3 tools/eval.py -c configs/ch_PP-OCRv2_det_pretrained_res18_0508.yml -o Global.checkpoints="checkpoints/enjp/ch_PP-OCR_res18_det/best_accuracy"  PostProcess.box_thresh=0.5 PostProcess.unclip_ratio=1.5