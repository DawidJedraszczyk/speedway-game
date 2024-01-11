#ifndef GAME_H
#define GAME_H

#include <vector>
#include <string>
#include <map>

class Game {
private:
    std::map<std::string, int> players_points;
    std::vector<std::pair<std::string, double>> previous_rounds_times;
    std::vector<std::pair<std::string, double>> current_round_times;
    int played_rounds = 0;
    bool game_ended = false;

public:
    void setGameEnded();
    bool getGameEnded() const;
    void addTime(const std::string& player, double time);
    size_t getCurrentRoundTimesSize() const;
    const std::vector<std::pair<std::string, double>>& getCurrentRoundTimes() const;
    void clearCurrentRoundTimes();
    int getCountOfPlayedRounds() const;
    void addPoints();
    void afterRoundCalculations();
    const std::map<std::string, int>& getPlayersPoints() const;
    int getPlayedRounds() const;
    const std::pair<std::string, double>& getBestTime();
    void sortPreviousTime();
};

#endif 
