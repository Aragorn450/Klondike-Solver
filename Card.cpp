#include "Card.h"
#include <iostream>

using namespace std;

void Card::Clear() {
  Rank = EMPTY;
  Suit = NONE;
}
void Card::Set(unsigned char value) {
  Value = value;
  Rank = (value % 13) + 1;
  Suit = value / 13;
  IsRed = Suit & 1 ? 0 : 1;
  IsOdd = Rank & 1;
  Foundation = Suit + 9;

  /*
    printf("Card::Set(%d):\n", Value);
    printf("  Rank: %d\n", Rank);
    printf("  Suit: %d\n", Suit);
    printf("  IsRed: %d\n", IsRed);
    printf("  IsOdd: %d\n", IsOdd);
    printf("  Foundation: %d\n", Foundation);
  */
}

unsigned char Card::GetSuit(unsigned char suit) {
  switch (toupper(suit)) {
    case 'H':
      return HEARTS;
      break;
    case 'S':
      return SPADES;
      break;
    case 'D':
      return DIAMONDS;
      break;
    case 'C':
      return CLUBS;
      break;
    default:
      return NONE;
  }
}

unsigned char Card::GetRank(unsigned char rank) {
  switch (toupper(rank)) {
    case 'A':
      return 1;
      break;
    case '2':
    case '3':
    case '4':
    case '5':
    case '6':
    case '7':
    case '8':
    case '9':
      return rank - 48;
      break;
    case 'T':
      return 10;
      break;
    case 'J':
      return 11;
      break;
    case 'Q':
      return 12;
      break;
    case 'K':
      return 13;
      break;
    default:
      return 0;
  }
}