#ifndef GAME_H
#define GAME_H

#include <vector>
#include <string>

class Game {
private:
    std::vector<std::pair<std::string, int>> points;
    std::vector<std::pair<std::string, double>> previous_races_times;
    std::vector<std::pair<std::string, double>> current_round_times;
    int played_rounds = 0;
    bool game_ended = false;

public:
    void addPoints(const std::string& player, int points);
    void setGameEnded();
    bool getGameEnded() const;
    void addTime(const std::string& player, double time);
    size_t getCurrentRoundTimesSize() const;
    const std::vector<std::pair<std::string, double>>& getCurrentRoundTimes() const;
    void add_played_round();
};

#endif 
