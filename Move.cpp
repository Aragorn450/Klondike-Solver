#include "Move.h"

Move::Move() {}
Move::Move(unsigned char from, unsigned char to, unsigned char count,
           unsigned char extra) {
  From = from;
  To = to;
  Count = count;
  Extra = extra;
}
void Move::Set(unsigned char from, unsigned char to, unsigned char count,
               unsigned char extra) {
  From = from;
  To = to;
  Count = count;
  Extra = extra;
}
bool Move::operator==(const Move &move) {
  return From == move.From && To == move.To && Count == move.Count &&
         Extra == move.Extra;
}

MoveNode::MoveNode(Move move) {
  Value = move;
  Parent = NULL;
}
MoveNode::MoveNode(Move move, shared_ptr<MoveNode> const &parent) {
  Value = move;
  Parent = parent;
}
