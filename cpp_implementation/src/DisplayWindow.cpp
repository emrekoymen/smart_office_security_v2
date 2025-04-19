#include "DisplayWindow.h"

DisplayWindow::DisplayWindow(const std::string& windowName) : windowName_(windowName) {
    cv::namedWindow(windowName_, cv::WINDOW_NORMAL);
}

void DisplayWindow::show(const cv::Mat& frame, int x, int y, int width, int height, float score, float fps) {
    cv::Mat disp = frame.clone();
    if (width > 0 && height > 0) {
        cv::rectangle(disp, cv::Rect(x, y, width, height), cv::Scalar(0, 255, 0), 2);
        std::string label = "Person: " + std::to_string(score);
        cv::putText(disp, label, cv::Point(x, y - 10), cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 255, 0), 2);
    }
    std::string fpsLabel = "FPS: " + std::to_string(fps);
    cv::putText(disp, fpsLabel, cv::Point(10, 30), cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(255, 0, 0), 2);
    cv::imshow(windowName_, disp);
}

void DisplayWindow::close() {
    cv::destroyWindow(windowName_);
}
