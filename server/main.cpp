#include <iostream>
#include <thread>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <cstring>
#include <filesystem>
#include <algorithm>
#include <omp.h>
#include <mutex>
#include <chrono>
#include <iomanip>
#include <sstream>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    #define close closesocket
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
#endif

namespace fs = std::filesystem;

class ParallelFileServer {
private:
    int serverPort;
    std::string serverDirectory;
    std::mutex logMutex;
    std::vector<std::thread> clientThreads;
    bool running;

    void logMessage(const std::string& message) {
        std::lock_guard<std::mutex> lock(logMutex);
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        std::tm* timeinfo = std::localtime(&time);
        std::stringstream ss;
        ss << std::put_time(timeinfo, "%Y-%m-%d %H:%M:%S");
        std::cout << "[" << ss.str() << "] " << message << std::endl;
    }

    std::vector<std::string> listFiles() {
        std::vector<std::string> files;
        try {
            for (const auto& entry : fs::directory_iterator(serverDirectory)) {
                if (entry.is_regular_file()) {
                    files.push_back(entry.path().filename().string());
                }
            }
        } catch (const std::exception& e) {
            logMessage("Error listing files: " + std::string(e.what()));
        }
        return files;
    }

    bool sendFile(int clientSocket, const std::string& filename) {
        std::string filepath = serverDirectory + "/" + filename;
        
        if (!fs::exists(filepath)) {
            std::string error = "FILE_NOT_FOUND";
            send(clientSocket, error.c_str(), error.length(), 0);
            return false;
        }

        std::ifstream file(filepath, std::ios::binary);
        if (!file.is_open()) {
            std::string error = "FILE_READ_ERROR";
            send(clientSocket, error.c_str(), error.length(), 0);
            return false;
        }

        // Get file size
        file.seekg(0, std::ios::end);
        size_t fileSize = file.tellg();
        file.seekg(0, std::ios::beg);

        // Send file size first
        std::string sizeStr = std::to_string(fileSize);
        send(clientSocket, sizeStr.c_str(), sizeStr.length(), 0);
        
        // Send delimiter
        const char* delimiter = "\n";
        send(clientSocket, delimiter, 1, 0);

        // Read file into memory first (for demonstration of parallel processing)
        std::vector<char> fileData(fileSize);
        file.read(fileData.data(), fileSize);
        file.close();
        
        // Use OpenMP to process file data in parallel
        // This demonstrates parallel processing - in production: checksum, compression, etc.
        const size_t chunkSize = 8192;
        size_t numChunks = (fileSize + chunkSize - 1) / chunkSize;
        
        #pragma omp parallel for
        for (size_t i = 0; i < numChunks; ++i) {
            size_t offset = i * chunkSize;
            size_t currentChunkSize = std::min(chunkSize, fileSize - offset);
            
            // Parallel processing of chunks (e.g., checksum calculation, data transformation)
            // For demonstration, we process each chunk
            char* chunkPtr = fileData.data() + offset;
            
            // Simulate parallel processing (in real scenario: compression, encryption, etc.)
            // This demonstrates OpenMP parallelism
            for (size_t j = 0; j < currentChunkSize; ++j) {
                // Processing operation (placeholder for actual parallel work)
                chunkPtr[j] = chunkPtr[j]; // Could apply transformations here
            }
        }
        
        // Send processed data sequentially (socket operations must be sequential)
        size_t totalSent = 0;
        const char* dataPtr = fileData.data();
        while (totalSent < fileSize) {
            size_t toSend = std::min(chunkSize, fileSize - totalSent);
            send(clientSocket, dataPtr + totalSent, toSend, 0);
            totalSent += toSend;
        }

        file.close();
        logMessage("File '" + filename + "' (" + std::to_string(fileSize) + " bytes) sent successfully");
        return true;
    }

    void handleClient(int clientSocket, struct sockaddr_in clientAddr) {
        char buffer[1024] = {0};
        std::string clientIP = inet_ntoa(clientAddr.sin_addr);
        logMessage("Client connected from " + clientIP);

        while (true) {
            memset(buffer, 0, sizeof(buffer));
            int bytesReceived = recv(clientSocket, buffer, sizeof(buffer) - 1, 0);
            
            if (bytesReceived <= 0) {
                break;
            }

            std::string request(buffer);
            request.erase(std::remove(request.begin(), request.end(), '\n'), request.end());
            request.erase(std::remove(request.begin(), request.end(), '\r'), request.end());

            logMessage("Request from " + clientIP + ": " + request);

            if (request == "LIST") {
                // Send list of files
                auto files = listFiles();
                std::string response;
                for (const auto& file : files) {
                    response += file + "\n";
                }
                if (response.empty()) {
                    response = "NO_FILES\n";
                }
                send(clientSocket, response.c_str(), response.length(), 0);
            }
            else if (request.find("GET ") == 0) {
                // Extract filename
                std::string filename = request.substr(4);
                sendFile(clientSocket, filename);
            }
            else if (request == "QUIT") {
                break;
            }
            else {
                std::string error = "UNKNOWN_COMMAND\n";
                send(clientSocket, error.c_str(), error.length(), 0);
            }
        }

        close(clientSocket);
        logMessage("Client " + clientIP + " disconnected");
    }

public:
    ParallelFileServer(int port, const std::string& directory) 
        : serverPort(port), serverDirectory(directory), running(false) {
        // Create directory if it doesn't exist
        if (!fs::exists(serverDirectory)) {
            fs::create_directories(serverDirectory);
        }
    }

    void start() {
        #ifdef _WIN32
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
            std::cerr << "WSAStartup failed" << std::endl;
            return;
        }
        #endif

        int serverSocket = socket(AF_INET, SOCK_STREAM, 0);
        if (serverSocket < 0) {
            logMessage("Error creating socket");
            return;
        }

        int opt = 1;
        setsockopt(serverSocket, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt));

        struct sockaddr_in serverAddr;
        serverAddr.sin_family = AF_INET;
        serverAddr.sin_addr.s_addr = INADDR_ANY;
        serverAddr.sin_port = htons(serverPort);

        if (bind(serverSocket, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) < 0) {
            logMessage("Error binding socket to port " + std::to_string(serverPort));
            close(serverSocket);
            return;
        }

        if (listen(serverSocket, 10) < 0) {
            logMessage("Error listening on socket");
            close(serverSocket);
            return;
        }

        running = true;
        logMessage("Parallel File Server started on port " + std::to_string(serverPort));
        logMessage("Serving files from: " + serverDirectory);
        logMessage("Waiting for connections...");

        while (running) {
            struct sockaddr_in clientAddr;
            socklen_t clientLen = sizeof(clientAddr);
            int clientSocket = accept(serverSocket, (struct sockaddr*)&clientAddr, &clientLen);

            if (clientSocket < 0) {
                continue;
            }

            // Create new thread for each client
            clientThreads.emplace_back([this, clientSocket, clientAddr]() {
                handleClient(clientSocket, clientAddr);
            });
        }

        close(serverSocket);
        #ifdef _WIN32
        WSACleanup();
        #endif
    }

    void stop() {
        running = false;
        for (auto& thread : clientThreads) {
            if (thread.joinable()) {
                thread.join();
            }
        }
    }
};

int main(int argc, char* argv[]) {
    int port = 8080;
    std::string directory = "server_files";

    if (argc > 1) {
        port = std::stoi(argv[1]);
    }
    if (argc > 2) {
        directory = argv[2];
    }

    // Set number of OpenMP threads
    omp_set_num_threads(4);

    ParallelFileServer server(port, directory);
    server.start();

    return 0;
}

