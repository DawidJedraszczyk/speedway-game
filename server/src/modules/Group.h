#ifndef GROUP_H
#define GROUP_H

#include <vector>
#include <string>
#include <mutex>
#include "Player.h"
#include "Game.h"

class Group {
private:
    std::vector<Player> players; //nickname, color
    std::vector<int> client_sockets;
    bool group_started = false;
    std::mutex mtx;
    Game game;

public:
    void addClient(int client_socket, const std::string& nickname, const std::string& color);
    std::vector<int>& getClients();
    std::string getNicknamesString() const;
    void sendToAllClients(const std::string& message);
    void handleClientMessages(int client_socket);
    void startGameTimer();
    bool getStarted() const;
};

#endif
