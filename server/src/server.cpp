#include <iostream>
#include <string>
#include <vector>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <cstring>
#include <thread>
#include <mutex>
#include <chrono>
#include <map>
#include <memory> 
#include "modules/Group.h"
#include <sstream>


std::vector<std::unique_ptr<Group>> groups;
std::mutex groups_mtx;


void handle_client(int client_socket) {
    char buffer[1024] = {0};
    read(client_socket, buffer, 1024);
    std::string nick(buffer);
    nick = nick.substr(0, nick.find('\n')); 

    std::lock_guard<std::mutex> lock(groups_mtx);
    
    // Check if a new group needs to be created
     if (groups.empty() || groups.back()->getClients().size() == 4 || groups.back()->getStarted()) {
        groups.emplace_back(std::make_unique<Group>());
    }

    Group& current_group = *groups.back();

    std::string color;
    switch (current_group.getClients().size()) {
        case 0: color = "red"; break;
        case 1: color = "blue"; break;
        case 2: color = "white"; break;
        case 3: color = "yellow"; break;
        default: color = "unknown";
    }

    current_group.addClient(client_socket, nick, color);
    std::thread message_thread(&Group::handleClientMessages, &current_group, client_socket);
    message_thread.detach();
    
    if (current_group.getClients().size() == 2 && !current_group.getStarted()) {
        std::thread timer_thread(&Group::startGameTimer, &current_group);
        timer_thread.detach();
        
    }

    std::string message = current_group.getNicknamesString();
    std::stringstream playersList;
    playersList << "PLAYERS: " << message << ";";
    current_group.sendToAllClients(playersList.str());

    if (current_group.getClients().size() == 4) {
        current_group.sendToAllClients("Squad is full");
    }
}

int main() {
    int server_fd, new_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);

    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt))) {
        perror("setsockopt");
        exit(EXIT_FAILURE);
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(8000);

    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    // Nasłuchiwanie
    if (listen(server_fd, 10) < 0) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    while (true) {
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
            perror("accept");
            exit(EXIT_FAILURE);
        }

        std::thread client_thread(handle_client, new_socket);
        client_thread.detach();
    }

    for (auto& group : groups) {
        for (int client_socket : group->getClients()) {
            close(client_socket);
        }
    }
    close(server_fd);

    return 0;
}