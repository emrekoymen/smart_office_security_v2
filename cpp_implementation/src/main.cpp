#include <iostream>
#include <string>
#include <chrono>
#include <thread>
#include <vector>
#include <opencv2/opencv.hpp>
#include "CameraStream.h"
#include "DisplayWindow.h"
#include "PersonDetector.h"
#include "ZigbeeSender.h"

void print_usage() {
    std::cout << "Usage: smart_office_security [--cam0 N] [--cam1 N] [--model_tpu PATH] [--threshold T] [--headless]" << std::endl;
}

int main(int argc, char** argv) {
    int cam0 = 0, cam1 = 2;
    std::string model_tpu = "../python_implementation/models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite";
    float threshold = 0.5f;
    bool headless = false;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--cam0" && i + 1 < argc) cam0 = std::stoi(argv[++i]);
        else if (arg == "--cam1" && i + 1 < argc) cam1 = std::stoi(argv[++i]);
        else if (arg == "--model_tpu" && i + 1 < argc) model_tpu = argv[++i];
        else if (arg == "--threshold" && i + 1 < argc) threshold = std::stof(argv[++i]);
        else if (arg == "--headless") headless = true;
        else { print_usage(); return 1; }
    }

    CameraStream cam_left(cam0), cam_right(cam1);
    cam_left.start();
    cam_right.start();

    PersonDetector detector(model_tpu, threshold);
    ZigbeeSender zigbee;

    DisplayWindow win_left("Camera 0"), win_right("Camera 1");

    while (true) {
        cv::Mat frame_left = cam_left.read();
        cv::Mat frame_right = cam_right.read();
        if (frame_left.empty() || frame_right.empty()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            continue;
        }

        // LEFT
        auto t0 = std::chrono::steady_clock::now();
        auto dets_left = detector.detect(frame_left);
        int x0=0, y0=0, w0=0, h0=0;
        float s0=0.0f;
        for (auto& d : dets_left) {
            x0 = d.x; y0 = d.y; w0 = d.w; h0 = d.h; s0 = d.score;
            // log
            std::cout << "Person Detected! (Confidence Score: " << s0 << ")" << std::endl;
            double ts = std::chrono::duration<double>(
                std::chrono::system_clock::now().time_since_epoch()).count();
            zigbee.sendEvent(ts, s0, {x0, y0, w0, h0});
            break; // only first
        }
        auto t1 = std::chrono::steady_clock::now();
        float fps0 = 1.0f / std::chrono::duration<float>(t1-t0).count();
        if (!headless) win_left.show(frame_left, x0, y0, w0, h0, s0, fps0);

        // RIGHT
        auto t2 = std::chrono::steady_clock::now();
        auto dets_right = detector.detect(frame_right);
        int x1=0, y1=0, w1=0, h1=0;
        float s1=0.0f;
        for (auto& d : dets_right) {
            x1 = d.x; y1 = d.y; w1 = d.w; h1 = d.h; s1 = d.score;
            std::cout << "Person Detected! (Confidence Score: " << s1 << ")" << std::endl;
            double ts = std::chrono::duration<double>(
                std::chrono::system_clock::now().time_since_epoch()).count();
            zigbee.sendEvent(ts, s1, {x1, y1, w1, h1});
            break;
        }
        auto t3 = std::chrono::steady_clock::now();
        float fps1 = 1.0f / std::chrono::duration<float>(t3-t2).count();
        if (!headless) win_right.show(frame_right, x1, y1, w1, h1, s1, fps1);

        if (!headless && (cv::waitKey(1) & 0xFF) == 'q') break;
    }

    cam_left.stop(); cam_right.stop();
    if (!headless) { win_left.close(); win_right.close(); cv::destroyAllWindows(); }
    return 0;
}
