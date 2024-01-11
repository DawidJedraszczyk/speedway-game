#include "Group.h"
#include <sys/socket.h>
#include <unistd.h>
#include <cstring>
#include <thread>
#include <chrono>
#include <iostream>
#include <regex>

void Group::addClient(int client_socket, const std::string& nickname, const std::string& color) {
    client_sockets.push_back(client_socket);
    players.push_back({nickname, color});
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
        playerStr += player.nickname + " (" + player.color + ")";
    }
    return playerStr;
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

void Group::sendToAllClients(const std::string& message) {
    for (int client_socket : client_sockets) {
        send(client_socket, message.c_str(), message.size(), 0);
    }
}

bool Group::getStarted() const {
    return group_started;
}

void Group::handleClientMessages(int client_socket) {
    char buffer[1024];
    std::regex timePattern("(red|blue|white|yellow)-TIME: ([0-9]+\\.[0-9]+)");

    while (true) {
        memset(buffer, 0, sizeof(buffer));
        int bytes_read = read(client_socket, buffer, sizeof(buffer) - 1);

        if (bytes_read <= 0) {
            std::cerr << "Client disconnected or error occurred. Socket: " << client_socket << std::endl;
            close(client_socket);
            break;
        }

        std::string message(buffer);
        std::smatch matches;
        std::pair<std::string, double> best_time;

        if (std::regex_search(message, matches, timePattern) && matches.size() > 2) {
            std::string player_nickname = matches[1].str();
            double player_time = std::stod(matches[2]);
            game.addTime(player_nickname, player_time);
            if (game.getCurrentRoundTimesSize() == players.size()){
                std::stringstream timesTable;
                for (const auto& time : game.getCurrentRoundTimes()) {
                    timesTable << "TIMES: " << time.first << ", " << time.second << ";";
                }
                sendToAllClients(timesTable.str());

                game.afterRoundCalculations();
                int played_rounds = game.getPlayedRounds();
                std::stringstream pointsTable;
                for (const auto& players_points : game.getPlayersPoints()){
                    pointsTable << "POINTS: " << players_points.first << ", " << players_points.second << ";";
                }
                sendToAllClients(pointsTable.str());

                if (played_rounds == 2){
                    best_time = game.getBestTime();
                    std::stringstream endGameMessage;
                    endGameMessage << "END: " << best_time.first << "," << best_time.second << ";";
                    sendToAllClients(endGameMessage.str());
                }
                else {
                    std::stringstream notEndGameMessage;
                    notEndGameMessage << "NEXT-ROUND:" << played_rounds << ";";
                    sendToAllClients(notEndGameMessage.str());
                }
            }
        }
        else {
            sendToAllClients(message);
        }
    }
}