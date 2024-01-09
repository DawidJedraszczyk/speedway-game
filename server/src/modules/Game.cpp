#include "Game.h"

void Game::addMove(const std::string& player, int x, int y) {
    moves.push_back({player, x, y});
}

void Game::addPoints(const std::string& player, int points) {
    this->points.push_back({player, points});
}

