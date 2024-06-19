

#export FLAGS_set_to_1d=False && export CUDA_VISIBLE_DEVICES=3 && python tools/infer/predict_det.py --det_algorithm="DB" --det_model_dir="./output/ocr20240313_2000/ch_PP-OCR_res18_det/inference_model/" --image_dir="./temp_img/" --use_gpu=True
#
export FLAGS_set_to_1d=False && export CUDA_VISIBLE_DEVICES=1 && python tools/infer/predict_det.py --det_algorithm="DB" --det_model_dir="./output/ocr20240418_s1_864/ch_PP-OCR_res18_det/inference_model/" --image_dir="datasets/ocr20240517_s2/valid/images" --use_gpu=True

#export FLAGS_set_to_1d=False && export CUDA_VISIBLE_DEVICES=0 && python tools/infer/predict_det.py --det_algorithm="DB" --det_model_dir="./output/ocr20240517_s2/ch_PP-OCR_res18_det/inference_model/" --image_dir="temp" --use_gpu=True
