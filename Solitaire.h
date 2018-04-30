#ifndef Solitaire_h
#define Solitaire_h
#include <memory>
#include <mutex>
#include <stack>
#include <string>
#include "Card.h"
#include "HashMap.h"
#include "Move.h"
#include "Pile.h"
#include "Random.h"
using namespace std;

enum SolveResult {
  CouldNotComplete = -2,
  SolvedMayNotBeMinimal = -1,
  Impossible = 0,
  SolvedMinimal = 1
};

struct MoveValue {
  Move move;
  int value;
};

class Solitaire {
 private:
  Move movesMade[512];
  Pile piles[13];
  Card cards[52];
  Move movesAvailable[32];
  MoveValue moveValue[100];
  int moveValueCount;
  Random random;
  int drawCount, roundCount, maxRoundCount;
  int foundationCount, movesAvailableCount, movesMadeCount;

  int FoundationMin();
  int GetTalonCards(Card talon[], int talonMoves[]);

 public:
  void Initialize();
  int Shuffle1(int dealNumber = -1);
  void Shuffle2(int dealNumber);
  void ResetGame();
  void ResetGame(int drawCount, int maxRoundCount = 11);
  void UpdateAvailableMoves();
  void MakeAutoMoves();
  void MakeMove(Move move);
  void MakeMove(int index);
  void UndoMove();
  SolveResult SolveMinimalMultithreaded(int numThreads, int maxClosedCount);
  SolveResult SolveMinimal(int maxClosedCount);
  SolveResult SolveFast(int maxClosedCount, int twoShift, int threeShift);
  SolveResult SolveRandom(int numberOfTimesToPlay, int solutionsToFind);
  int MovesAvailableCount();
  int MovesMadeCount();
  int MovesMadeNormalizedCount();
  int FoundationCount();
  int RoundCount();
  int DrawCount();
  int MovesAdded(Move const &move);
  int MinimumMovesLeft();
  void SetMaxRoundCount(int maxRoundCount);
  void SetDrawCount(int drawCount);
  HashKey GameState();
  string GetMoveInfo(Move move);
  bool sampleGames(const int initialValues[], int sampleCount, int values[],
                   int dealNumber = -1);
  bool setCards(const int values[], const int sizes[]);
  bool LoadSolitaire(string const &cardSet);
  string GetSolitaire();
  bool LoadPysol(string const &cardSet);
  string GetPysol();
  Move GetMoveAvailable(int index);
  Move GetMoveMade(int index);
  string GameDiagram();
  string GameDiagramPysol();
  string MovesMade();
  string MovesAvailable();
  Move operator[](int index);
  int MoveValueCount();
  MoveValue GetMoveValue(int i);
};

class SolitaireWorker {
 private:
  stack<shared_ptr<MoveNode>> open[512];
  Move bestSolution[512];
  Solitaire *solitaire;
  mutex mtx;
  int openCount, maxFoundationCount, bestSolutionMoveCount, startMoves,
      maxClosedCount;

  void RunMinimalWorker(void *closed);
  void RunFastWorker();

 public:
  SolitaireWorker(Solitaire &solitaire, int maxClosedCount);

  SolveResult Run(int numThreads);
};
#endif
