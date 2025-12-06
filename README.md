# 🧪 Water Sort Puzzle with Artificial Intelligence

![Project Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Course](https://img.shields.io/badge/Course-Konsep_Kecerdasan_Artifisial-blue)
![Language](https://img.shields.io/badge/Language-Python-yellow) > **Final Project - Group 5 (KKA C)** > A smarter implementation of the classic Water Sort Puzzle. Unlike conventional games with static levels, this project utilizes **Artificial Intelligence** to generate guaranteed solvable levels procedurally and provides optimal hints using pathfinding algorithms.

## 👥 The Team (Group 5)
* **Syah Amin Zikri** (5025241195)
* **Aziz Adi Pramana** (5025241197)
* **M. Sholihuddin Rizky** (5025241171)

---

## 🚀 Key Features

### 1. Procedural Level Generation (No Database!)
Conventional puzzles use static level databases, which can get boring. We implemented a **Level Generator** that creates unique levels in real-time.
* **Guaranteed Solvability:** No "impossible" levels. Every generated puzzle has a valid solution.
* **Dynamic Difficulty:** The complexity is scaled based on the recursion depth of the generator.

### 2. Smart Hint System
Stuck? Our hint system doesn't just give you a random legal move. It calculates the **optimal path** to the solution and guides you one step at a time.

### 3. Strategic Gameplay
* **Extra Tube Mode:** Add an empty bottle if you are cornered.
* **Trade-off System:** Using Hints or Extra Tubes costs "Stars" (score), forcing players to think before assisting.

---

## 🧠 The AI Behind It

This project models the game as a **State-Space Search** problem. We utilize two core algorithms:

### A. Reverse BFS (Breadth-First Search) - *For Level Generation*
Instead of creating a random mess and checking if it's solvable (which risks deadlocks), we use **Reverse Engineering** logic:
1.  **Start:** Begin with a solved state (all bottles sorted).
2.  **Action:** Simulate "pouring backward" (mixing colors) using BFS.
3.  **Stop:** Stop when the desired difficulty depth is reached.
4.  **Result:** The final mixed state becomes the puzzle for the player.

### B. A* (A-Star) Search - *For Smart Hints*
To find the best move, we use the A* algorithm with the cost function:
$$f(n) = g(n) + h(n)$$
* $g(n)$: Cost of the path so far.
* $h(n)$: **Heuristic Function**. We calculate a "Chaos Score" based on how mixed the colors are within a single bottle.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
