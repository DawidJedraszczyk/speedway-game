#include "Game.h"
#include <string>

void Game::addPoints(const std::string& player, int points) {
    this->points.push_back({player, points});
}

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

void Game::add_played_round() {
    this->played_rounds += 1;
}