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
    socketToColorMap[client_socket] = color;
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
    for (int i = 30; i > 0; --i) {
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
            std::stringstream disconnectedPlayer;
            disconnectedPlayer << "DISCONNECTED: " << getColorBySocket(client_socket) << ";";
            close(client_socket);
            removeClient(client_socket);
            sendToAllClients(disconnectedPlayer.str());
            if (getClients().size() < 2){
                endGame();
            }
            break;
        }

        std::string message(buffer);
        std::smatch matches;
        std::pair<std::string, double> best_time;

        if (std::regex_search(message, matches, timePattern) && matches.size() > 2) {
            std::string player_nickname = matches[1].str();
            double player_time = std::stod(matches[2]);
            game.addTime(player_nickname, player_time);
            if (game.getCurrentRoundTimesSize() == getClients().size()){
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

                if (played_rounds == 4){
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

std::string Group::getColorBySocket(int client_socket) const {
    auto it = socketToColorMap.find(client_socket);
    if (it != socketToColorMap.end()) {
        return it->second;
    }
    return ""; 
}

void Group::removeClient(int client_socket) {
    client_sockets.erase(std::remove(client_sockets.begin(), client_sockets.end(), client_socket), client_sockets.end());
    socketToColorMap.erase(client_socket);
}

void Group::endGame() {
    game.setGameEnded();
    std::stringstream endGameMessage;
    if (game.getCountOfPlayedRounds() > 0){
        std::pair<std::string, double> best_time;
        best_time = game.getBestTime(); 
        endGameMessage << "END: " << best_time.first << "," << best_time.second << ";";
    }
    else {
        endGameMessage << "END: " << "None" << "," << "None" << ";";;
    }
    sendToAllClients(endGameMessage.str());

    for (int client_socket : client_sockets) {
        close(client_socket);
    }

    client_sockets.clear();
}