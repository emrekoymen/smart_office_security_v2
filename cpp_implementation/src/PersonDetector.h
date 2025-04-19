#pragma once

#include <string>
#include <vector>
#include <opencv2/opencv.hpp>
#include <tensorflow/lite/c/c_api.h>
#include <edgetpu_c.h>

struct DetectedObject {
    int x;
    int y;
    int w;
    int h;
    float score;
};

class PersonDetector {
public:
    PersonDetector(const std::string& model_path, float threshold = 0.5f);
    ~PersonDetector();

    std::vector<DetectedObject> detect(const cv::Mat& frame);

private:
    TfLiteModel* model_;
    TfLiteInterpreterOptions* options_;
    TfLiteInterpreter* interpreter_;
    TfLiteDelegate* delegate_;
    float threshold_;
};
