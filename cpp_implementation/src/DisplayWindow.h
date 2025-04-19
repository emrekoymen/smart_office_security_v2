#pragma once

#include <opencv2/opencv.hpp>
#include <string>

class DisplayWindow {
public:
    DisplayWindow(const std::string& windowName);
    void show(const cv::Mat& frame, int x, int y, int width, int height, float score, float fps);
    void close();

private:
    std::string windowName_;  
};
