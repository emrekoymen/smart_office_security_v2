#include "ZigbeeSender.h"
#include <iostream>
#include <sstream>

using namespace boost::asio;

ZigbeeSender::ZigbeeSender(const std::string& port, unsigned int baudrate)
    : io_(), serial_(io_) {
  try {
    serial_.open(port);
    serial_.set_option(serial_port_base::baud_rate(baudrate));
  } catch (std::exception& e) {
    std::cerr << "[Zigbee] Serial init failed: " << e.what() << std::endl;
  }
}

ZigbeeSender::~ZigbeeSender() {
  close();
}

void ZigbeeSender::sendEvent(double timestamp, float confidence, const std::vector<int>& bbox) {
  if (!serial_.is_open()) {
    std::cerr << "[Zigbee] Serial not open!" << std::endl;
    return;
  }
  std::ostringstream oss;
  oss << "{\"timestamp\":" << timestamp
      << ",\"confidence\":" << confidence
      << ",\"bbox\":[" << bbox[0] << "," << bbox[1] << "," << bbox[2] << "," << bbox[3] << "]}\n";
  write(serial_, buffer(oss.str()));
}

void ZigbeeSender::close() {
  if (serial_.is_open()) serial_.close();
}
