#include "PersonDetector.h"
#include <iostream>

PersonDetector::PersonDetector(const std::string& model_path, float threshold)
    : model_(nullptr), options_(nullptr), interpreter_(nullptr), delegate_(nullptr), threshold_(threshold) {
  model_ = TfLiteModelCreateFromFile(model_path.c_str());
  if (!model_) {
    std::cerr << "[ERROR] Failed to load model: " << model_path << std::endl;
    return;
  }
  options_ = TfLiteInterpreterOptionsCreate();
  // Create Edge TPU delegate (USB)
  delegate_ = edgetpu_create_delegate(EDGETPU_APEX_USB, nullptr, nullptr, 0);
  if (!delegate_) {
    std::cerr << "[ERROR] Failed to create Edge TPU delegate" << std::endl;
  } else {
    TfLiteInterpreterOptionsAddDelegate(options_, delegate_);
  }
  interpreter_ = TfLiteInterpreterCreate(model_, options_);
  if (!interpreter_) {
    std::cerr << "[ERROR] Failed to create interpreter" << std::endl;
    return;
  }
  if (TfLiteInterpreterAllocateTensors(interpreter_) != kTfLiteOk) {
    std::cerr << "[ERROR] Failed to allocate tensors" << std::endl;
  }
}

PersonDetector::~PersonDetector() {
  if (interpreter_) TfLiteInterpreterDelete(interpreter_);
  if (options_) TfLiteInterpreterOptionsDelete(options_);
  if (delegate_) edgetpu_free_delegate(delegate_);
  if (model_) TfLiteModelDelete(model_);
}

std::vector<DetectedObject> PersonDetector::detect(const cv::Mat& frame) {
  std::vector<DetectedObject> results;
  if (!interpreter_) return results;
  // Resize and prepare input
  cv::Mat resized;
  cv::resize(frame, resized, cv::Size(300, 300));
  if (resized.empty()) return results;
  TfLiteTensor* input_tensor = TfLiteInterpreterGetInputTensor(interpreter_, 0);
  TfLiteTensorCopyFromBuffer(input_tensor, resized.data, resized.total() * resized.elemSize());
  // Run inference
  if (TfLiteInterpreterInvoke(interpreter_) != kTfLiteOk) {
    std::cerr << "[ERROR] Inference failed" << std::endl;
    return results;
  }
  // Get outputs
  const TfLiteTensor* boxes = TfLiteInterpreterGetOutputTensor(interpreter_, 0);
  const TfLiteTensor* classes = TfLiteInterpreterGetOutputTensor(interpreter_, 1);
  const TfLiteTensor* scores = TfLiteInterpreterGetOutputTensor(interpreter_, 2);
  const TfLiteTensor* count = TfLiteInterpreterGetOutputTensor(interpreter_, 3);
  int num = static_cast<int>(*reinterpret_cast<float*>(TfLiteTensorData(count)));
  int h = frame.rows;
  int w = frame.cols;
  float* boxes_data = reinterpret_cast<float*>(TfLiteTensorData(boxes));
  float* classes_data = reinterpret_cast<float*>(TfLiteTensorData(classes));
  float* scores_data = reinterpret_cast<float*>(TfLiteTensorData(scores));
  for (int i = 0; i < num; ++i) {
    if (static_cast<int>(classes_data[i]) == 0 && scores_data[i] > threshold_) {
      float ymin = boxes_data[4 * i];
      float xmin = boxes_data[4 * i + 1];
      float ymax = boxes_data[4 * i + 2];
      float xmax = boxes_data[4 * i + 3];
      DetectedObject obj;
      obj.x = static_cast<int>(xmin * w);
      obj.y = static_cast<int>(ymin * h);
      obj.w = static_cast<int>((xmax - xmin) * w);
      obj.h = static_cast<int>((ymax - ymin) * h);
      obj.score = scores_data[i];
      results.push_back(obj);
    }
  }
  return results;
}
