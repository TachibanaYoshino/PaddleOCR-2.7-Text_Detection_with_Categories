import os,json

def Labelmejson_to_ppDBdet(path, label_path, label):
    img_files = os.listdir(path)
    ans = ''
    for file in img_files:
        prefilename = os.path.splitext(file)[0]
        postfilename = os.path.splitext(file)[1]
        if postfilename.lower() == ".jpg" or postfilename.lower() == ".jpeg" or postfilename.lower() == ".png":
            if  os.path.exists(os.path.join(path, prefilename + ".json")) :
                with open(os.path.join(path, prefilename + ".json"), "r") as f:
                    json_shapes = json.load(f)["shapes"]
                if len(json_shapes)<1:
                    continue
                else:
                    datas = []
                    for info in json_shapes:
                        if info["label"].split('-')[0] in label:
                            coor = {}
                            coor["transcription"] = info["label"].split('-')[0]
                            temp_points = info['points']
                            pps = []
                            for p in temp_points:
                                pps.append([int(p[0]), int(p[1])])
                            # temp_points = np.array(temp_points)
                            # xmin, ymin = [int(x) for x in temp_points.min(axis=0)]
                            # xmax, ymax = [int(x) for x in temp_points.max(axis=0)]
                            # pps = [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]
                            coor["points"] = pps
                            datas.append(coor)
                ans = ans + f"images/{file}" + "\t" + json.dumps(datas) + '\n'
                # print('\t'.join([f"images/{file}"  , json.dumps(datas)]) == ' '.join([f"images/{file}"  , json.dumps(datas)]))
    with open(label_path, 'w') as outfile:
        outfile.write(ans)


if __name__ == "__main__":
    label = {'en': 0, 'jpn': 1}
    # Labelmejson_to_ppDBdet(path=r"E:\ada\PaddleOCR-release-2.7\datasets\enjp\train\images", label_path=r"E:\ada\PaddleOCR-release-2.7\datasets\enjp\train\train.txt", label=label)
    Labelmejson_to_ppDBdet(path=r"E:\ada\PaddleOCR-release-2.7\datasets\enjp\test\images", label_path=r"E:\ada\PaddleOCR-release-2.7\datasets\enjp\test\test.txt", label=label)