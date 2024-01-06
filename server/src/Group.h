#ifndef GROUP_H
#define GROUP_H

#include <vector>
#include <string>
#include <mutex>

class Group {
private:
    std::vector<std::pair<std::string, std::string>> players; //nickname, color
    std::vector<int> client_sockets;
    bool group_started = false;
    std::mutex mtx;

public:
    void addClient(int client_socket, const std::string& nickname, const std::string& color);
    std::vector<int>& getClients();
    std::string getNicknamesString() const;
    bool getStarted() const;
    void setStarted();
    void sendToAllClients(const std::string& message);
    void startGameTimer();
};

#endif
