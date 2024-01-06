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
