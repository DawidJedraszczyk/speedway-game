#ifndef GAME_H
#define GAME_H

#include <vector>
#include "Group.h"
#include "Move.h"
#include "Point.h"

class Game {
private:
    Group grupa;
    std::vector<Move> moves;
    std::vector<Point> points;

public:
    void addMove(const std::string& player, int x, int y);
    void addPoints(const std::string& player, int points);
};

#endif 
