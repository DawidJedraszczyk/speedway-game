#include "Game.h"
#include <string>
#include <algorithm>
#include <map>
#include <iostream>

void Game::setGameEnded() {
    game_ended = true;
}

bool Game::getGameEnded() const {
    return game_ended;
}

void Game::addTime(const std::string& player, double time) {
    this->current_round_times.push_back({player, time});
}

size_t Game::getCurrentRoundTimesSize() const {
    return current_round_times.size();
}

const std::vector<std::pair<std::string, double>>& Game::getCurrentRoundTimes() const {
    return current_round_times;
}

void Game::clearCurrentRoundTimes() {
    this->previous_rounds_times.insert(previous_rounds_times.end(), current_round_times.begin(), current_round_times.end());
    current_round_times.clear(); // Optionally clear current_round_times
}

int Game::getCountOfPlayedRounds() const {
    return played_rounds;
}

void Game::addPoints() {
    std::sort(current_round_times.begin(), current_round_times.end(),
              [](const std::pair<std::string, double>& a, const std::pair<std::string, double>& b) {
                  return a.second < b.second;
              });

    int points_award = 3;
    for (const auto& players_times : current_round_times){
        players_points[players_times.first] += points_award;
        points_award -= 1;
    }
}

void Game::afterRoundCalculations() {
    this->played_rounds += 1;
    addPoints();
    clearCurrentRoundTimes();
}

const std::map<std::string, int>& Game::getPlayersPoints() const {
    return players_points;
}

int Game::getPlayedRounds() const {
    return played_rounds;
}

const std::pair<std::string, double>& Game::getBestTime() {
    sortPreviousTime();
    return previous_rounds_times.front();
}

void Game::sortPreviousTime() {
    std::sort(previous_rounds_times.begin(), previous_rounds_times.end(), 
        [](const std::pair<std::string, double>& a, const std::pair<std::string, double>& b) {
            return a.second < b.second;
        });
}