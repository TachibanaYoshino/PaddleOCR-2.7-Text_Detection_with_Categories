
# export FLAGS_set_to_1d=False && export CUDA_VISIBLE_DEVICES=3 && python tools/infer_det.py -c configs/ch_PP-OCRv2_det_pretrained_res18.yml -o Global.checkpoints="checkpoints/enjp/ch_PP-OCR_res18_det/best_accuracy"  PostProcess.box_thresh=0.5 PostProcess.unclip_ratio=1.8
 export FLAGS_set_to_1d=False && export CUDA_VISIBLE_DEVICES=3 && python tools/infer_det.py -c configs/ch_PP-OCRv2_det_pretrained_res18.yml -o Global.checkpoints="checkpoints/enjp/ch_PP-OCR_res18_det/best_accuracy"  PostProcess.box_thresh=0.5 PostProcess.unclip_ratio=2.0 Global.infer_img="./data/test_data1" Global.save_res_path="./output/enjp/ch_PP-OCR_res18_det/test_data1/predicts_db.txt"

