# recommended paddle.__version__ == 2.0.0
#python3 -m paddle.distributed.launch --log_dir=./debug/ --gpus '0,1,2,3,4,5,6,7'  tools/train.py -c configs/rec/rec_mv3_none_bilstm_ctc.yml


export FLAGS_set_to_1d=False && export CUDA_VISIBLE_DEVICES=1 && python tools/train.py -c configs/ch_PP-OCRv2_det_pretrained_res18.yml


