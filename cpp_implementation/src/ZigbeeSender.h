#pragma once

#include <boost/asio.hpp>
#include <string>
#include <vector>

class ZigbeeSender {
public:
    ZigbeeSender(const std::string& port = "/dev/ttyUSB0", unsigned int baudrate = 9600);
    ~ZigbeeSender();

    void sendEvent(double timestamp, float confidence, const std::vector<int>& bbox);
    void close();

private:
    boost::asio::io_service io_;
    boost::asio::serial_port serial_;
};
