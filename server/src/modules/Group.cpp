#include "Group.h"
#include <sys/socket.h>
#include <unistd.h>
#include <cstring>
#include <thread>
#include <chrono>
#include <iostream>

void Group::addClient(int client_socket, const std::string& nickname, const std::string& color) {
    client_sockets.push_back(client_socket);
    players.push_back(std::make_pair(nickname, color));
}

std::vector<int>& Group::getClients() {
    return client_sockets;
}

std::string Group::getNicknamesString() const {
    std::string playerStr;
    for (const auto& player : players) {
        if (!playerStr.empty()) {
            playerStr += ", ";
        }
        playerStr += player.first + " (" + player.second + ")"; // Concatenating nickname and color
    }
    return playerStr;
}

bool Group::getStarted() const {
    return group_started;
}

void Group::setStarted() {
    group_started = true;
}

void Group::sendToAllClients(const std::string& message) {
    std::cout << "message: " << message << std::endl; // Debug print
    for (int client_socket : client_sockets) {
        send(client_socket, message.c_str(), message.size(), 0);
    }
}

void Group::startGameTimer() {
    for (int i = 5; i > 0; --i) {
        std::lock_guard<std::mutex> lock(mtx);
        if (group_started) {
            return;
        }
        std::string message = "Game starts in: " + std::to_string(i) + " seconds";
        sendToAllClients(message);
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    {
        std::lock_guard<std::mutex> lock(mtx);
        group_started = true;
        sendToAllClients("Game started");
    }
}

void Group::handleClientMessages(int client_socket) {
    char buffer[1024];

    while (true) {
        memset(buffer, 0, sizeof(buffer));
        int bytes_read = read(client_socket, buffer, sizeof(buffer) - 1);

        if (bytes_read <= 0) {
            // Handle disconnection or error
            std::cerr << "Client disconnected or error occurred. Socket: " << client_socket << std::endl;
            close(client_socket);  // Close the socket to release resources
            break;
        }

        std::string message(buffer);
        std::cout << "Received message from socket " << client_socket << ": " << message << std::endl;

        // Optionally, you can add further processing of the message here.
        sendToAllClients(message);
    }
}