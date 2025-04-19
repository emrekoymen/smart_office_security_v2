#pragma once

#include <opencv2/opencv.hpp>
#include <thread>
#include <atomic>
#include <mutex>

class CameraStream {
public:
  CameraStream(int src, int width = 640, int height = 480, int fps = 20);
  ~CameraStream();
  void start();
  cv::Mat read();
  void stop();

private:
  void update();
  int src_; int width_; int height_; int fps_;
  cv::VideoCapture cap_;
  cv::Mat frame_;
  std::atomic<bool> stopped_;
  std::mutex mtx_;
  std::thread thread_;
};
