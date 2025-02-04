# Face Detection Model

## Introduction
`face_detection` High efficiency, high speed face detection solutions, including the most advanced models and classic models.

![](../../docs/images/12_Group_Group_12_Group_Group_12_935.jpg)

## Model Library

#### A mAP on the WIDERFACE dataset

| Network structure | size | images/GPUs | Learning rate strategy | Easy/Medium/Hard Set  | Prediction delay（SD855）| Model size(MB) | Download | Configuration File |
|:------------:|:--------:|:----:|:-------:|:-------:|:---------:|:----------:|:---------:|:--------:|
| BlazeFace  | 640  |    8    | 1000e     | 0.885 / 0.855 / 0.731 | - | 0.472 |[link](https://paddledet.bj.bcebos.com/models/blazeface_1000e.pdparams) | [Configuration File](https://github.com/PaddlePaddle/PaddleDetection/tree/develop/configs/face_detection/blazeface_1000e.yml) |
| BlazeFace-FPN-SSH  | 640  |    8    | 1000e     | 0.907 / 0.883 / 0.793 | - | 0.479 |[link](https://paddledet.bj.bcebos.com/models/blazeface_fpn_ssh_1000e.pdparams) | [Configuration File](https://github.com/PaddlePaddle/PaddleDetection/tree/develop/configs/face_detection/blazeface_fpn_ssh_1000e.yml) |

**Attention:**  
- We use a multi-scale evaluation strategy to get the mAP in `Easy/Medium/Hard Set`. Please refer to the [evaluation on the WIDER FACE dataset](#Evaluated-on-the-WIDER-FACE-Dataset) for details.

## Quick Start

### Data preparation
We use [WIDER-FACE dataset](http://shuoyang1213.me/WIDERFACE/) for training and model tests, the official web site provides detailed data is introduced.
- WIDER-Face data source:  
- Load a dataset of type `wider_face` using the following directory structure:
  ```
  dataset/wider_face/
  ├── wider_face_split
  │   ├── wider_face_train_bbx_gt.txt
  │   ├── wider_face_val_bbx_gt.txt
  ├── WIDER_train
  │   ├── images
  │   │   ├── 0--Parade
  │   │   │   ├── 0_Parade_marchingband_1_100.jpg
  │   │   │   ├── 0_Parade_marchingband_1_381.jpg
  │   │   │   │   ...
  │   │   ├── 10--People_Marching
  │   │   │   ...
  ├── WIDER_val
  │   ├── images
  │   │   ├── 0--Parade
  │   │   │   ├── 0_Parade_marchingband_1_1004.jpg
  │   │   │   ├── 0_Parade_marchingband_1_1045.jpg
  │   │   │   │   ...
  │   │   ├── 10--People_Marching
  │   │   │   ...
  ```

- Manually download the dataset:
To download the WIDER-FACE dataset, run the following command:
```
cd dataset/wider_face && ./download_wider_face.sh
```

### Parameter configuration
The configuration of the base model can be referenced to `configs/face_detection/_base_/blazeface.yml`；
Improved model to add FPN and SSH neck structure, configuration files can be referenced to `configs/face_detection/_base_/blazeface_fpn.yml`, You can configure FPN and SSH as required
```yaml
BlazeNet:
   blaze_filters: [[24, 24], [24, 24], [24, 48, 2], [48, 48], [48, 48]]
   double_blaze_filters: [[48, 24, 96, 2], [96, 24, 96], [96, 24, 96],
                           [96, 24, 96, 2], [96, 24, 96], [96, 24, 96]]
   act: hard_swish #Configure Blaze Block activation function in Backbone. The basic model is Relu. hard_swish is needed to add FPN and SSH

BlazeNeck:
   neck_type : fpn_ssh #only_fpn, only_ssh and fpn_ssh
   in_channel: [96,96]
```



### Training and Evaluation
The training process and evaluation process methods are consistent with other algorithms, please refer to [GETTING_STARTED_cn.md](../../docs/tutorials/GETTING_STARTED_cn.md)。  
**Attention:** Face detection models currently do not support training and evaluation.

#### Evaluated on the WIDER-FACE Dataset
- Step 1: Evaluate and generate a result file:
```shell
python -u tools/eval.py -c configs/face_detection/blazeface_1000e.yml \
       -o weights=output/blazeface_1000e/model_final \
       multi_scale=True
```
Set `multi_scale=True` for multi-scale evaluation. After evaluation, test results in TXT format will be generated in `output/pred`.

- Step 2: Download the official evaluation script and Ground Truth file:
```
wget http://mmlab.ie.cuhk.edu.hk/projects/WIDERFace/support/eval_script/eval_tools.zip
unzip eval_tools.zip && rm -f eval_tools.zip
```

- Step 3: Start the evaluation

Method 1: Python evaluation:
```
git clone https://github.com/wondervictor/WiderFace-Evaluation.git
cd WiderFace-Evaluation
# compile
python3 setup.py build_ext --inplace
# Begin to assess
python3 evaluation.py -p /path/to/PaddleDetection/output/pred -g /path/to/eval_tools/ground_truth
```

Method 2: MatLab evaluation:
```
# Change the name of save result path and draw curve in `eval_tools/wider_eval.m`:
pred_dir = './pred';  
legend_name = 'Paddle-BlazeFace';

`wider_eval.m` is the main implementation of the evaluation module. Run the following command:
matlab -nodesktop -nosplash -nojvm -r "run wider_eval.m;quit;"
```

### Use by Python Code
In order to support development, here is an example of using the Paddle Detection whl package to make predictions through Python code.
```python
import cv2
import paddle
import numpy as np
from ppdet.core.workspace import load_config
from ppdet.engine import Trainer
from ppdet.metrics import get_infer_results
from ppdet.data.transform.operators import NormalizeImage, Permute


if __name__ == '__main__':
    # prepare for the parameters
    config_path = 'PaddleDetection/configs/face_detection/blazeface_1000e.yml'
    cfg = load_config(config_path)
    weight_path = 'PaddleDetection/output/blazeface_1000e.pdparams'
    infer_img_path = 'PaddleDetection/demo/hrnet_demo.jpg'
    cfg.weights = weight_path
    bbox_thre = 0.8
    paddle.set_device('gpu')
    # create the class object
    trainer = Trainer(cfg, mode='test')
    trainer.load_weights(cfg.weights)
    trainer.model.eval()
    normaler = NormalizeImage(mean=[123, 117, 104], std=[127.502231, 127.502231, 127.502231], is_scale=False)
    permuter = Permute()
    # read the image file
    im = cv2.imread(infer_img_path)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    # prepare for the data dict
    data_dict = {'image': im}
    data_dict = normaler(data_dict)
    data_dict = permuter(data_dict)
    h, w, c = im.shape
    data_dict['im_id'] = paddle.Tensor(np.array([[0]]))
    data_dict['im_shape'] = paddle.Tensor(np.array([[h, w]], dtype=np.float32))
    data_dict['scale_factor'] = paddle.Tensor(np.array([[1., 1.]], dtype=np.float32))
    data_dict['image'] = paddle.Tensor(data_dict['image'].reshape((1, c, h, w)))
    data_dict['curr_iter'] = paddle.Tensor(np.array([0]))
    # do the prediction
    outs = trainer.model(data_dict)
    # to do the postprocess to get the final bbox info
    for key in ['im_shape', 'scale_factor', 'im_id']:
        outs[key] = data_dict[key]
    for key, value in outs.items():
        outs[key] = value.numpy()
    clsid2catid, catid2name = {0: 'face'}, {0: 0}
    batch_res = get_infer_results(outs, clsid2catid)
    bbox = [sub_dict for sub_dict in batch_res['bbox'] if sub_dict['score'] > bbox_thre]
    print(bbox)
```


## Citations

```
@article{bazarevsky2019blazeface,
      title={BlazeFace: Sub-millisecond Neural Face Detection on Mobile GPUs},
      author={Valentin Bazarevsky and Yury Kartynnik and Andrey Vakunov and Karthik Raveendran and Matthias Grundmann},
      year={2019},
      eprint={1907.05047},
      archivePrefix={arXiv},
```
