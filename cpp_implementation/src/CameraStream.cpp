#include "CameraStream.h"
#include <chrono>

CameraStream::CameraStream(int src, int width, int height, int fps)
    : src_(src), width_(width), height_(height), fps_(fps), cap_(src), stopped_(false) {
    cap_.set(cv::CAP_PROP_FRAME_WIDTH, width_);
    cap_.set(cv::CAP_PROP_FRAME_HEIGHT, height_);
    cap_.set(cv::CAP_PROP_FPS, fps_);
}

CameraStream::~CameraStream() {
    stop();
}

void CameraStream::start() {
    thread_ = std::thread(&CameraStream::update, this);
}

cv::Mat CameraStream::read() {
    std::lock_guard<std::mutex> lock(mtx_);
    return frame_.clone();
}

void CameraStream::stop() {
    stopped_ = true;
    if (thread_.joinable()) thread_.join();
    cap_.release();
}

void CameraStream::update() {
    while (!stopped_) {
        cv::Mat frame;
        if (!cap_.read(frame)) continue;
        {
            std::lock_guard<std::mutex> lock(mtx_);
            frame_ = frame.clone();
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1000 / fps_));
    }
}
