# py-msa-kdenlive
Python script to load a [Kdenlive](https://kdenlive.org/en/) (OSS NLE video editor) project file, and conform the edit on video or numpy arrays.

I used this to create [www.deepmeditations.ai](www.deepmeditations.ai) (editing video snippets exported from a Generative Adversarial Network, and conforming that edit on numpy arrays of z-sequences).

More information and motivations at
https://medium.com/@memoakten/deep-meditations-meaningful-exploration-of-ones-inner-self-576aab2f3894

# Installation
Clone or download the repo, and install dependencies with ```pip install -r requirements.txt```.
If I've missed anything (very possible - I extracted this from a much larger set of packages I've been developing and working with) please file an issue. I've only tested this with python 2.7 on Ubuntu, but I think it should work on any OS, and with python 3.x too.

# Usage
You can run the python script ```run.py``` with the command line arguments:

    -k, --kdenlive_prj_path # path to kdenlive project
    -n, --track_name # name of track in kdenlive project to use
    -i, --input_path # path to input numpy array (e.g. containing z-sequence) or video file
    -g, --groundtruth_path # [OPTIONAL] path to ground truth edited array or video file (for checking functionality)
    -o, --output_path # path to desired output numpy array containing conformed sequence
    -v, --verbose # if 1, dumps entire edit to console (comparing to ground truth if available)

e.g.

    python run.py \
        --kdenlive_prj_path "./testdata/test.kdenlive" \
        --track_name "Video 1" \
        --input_path "./testdata/z_orig.npy" \
        --groundtruth_path "./testdata/z_edited.npy" \
        --output_path "z_out.npy" \
        --verbose 0


You can look at the contents of:

* ```test_npy.sh``` and ```test_video.sh``` for examples on how to use the script.
* ```run.py``` to see the code on how to use the python API
* ```./msa/kdenlive/kdenlive.py``` to see the main source and full API.


# Citation
Paper to be presented at the 2nd Workshop on Machine Learning for Creativity and Design at the 32nd Conference on Neural Information Processing Systems (NeurIPS) 2018. If you find this useful, please cite the paper:

    @article{deepmeditations2018,
      title={Deep Meditations: Controlled navigation of latent space},
      author={Akten, Memo and Fiebrink, Rebecca and Grierson, Mick},
      journal={NeurIPS, Workshop on Machine Learning for Creativity and Design},
      year={2018}
    }
