#include <iostream>
#include <queue>
#include <vector>
#include <algorithm>
#include <cstring>
#include <ctime>
#include <iomanip>

using namespace std;

enum ProcessState { READY, RUNNING, FINISHED };

struct PCB {
    char name[10];
    int priority;
    int burstTime;
    int remainingTime;
    int arrivalTime;
    int waitingTime;
    int turnaroundTime;
    int completionTime;
    ProcessState state;
    
    PCB(const char* n = "", int p = 0, int b = 0, int a = 0) {
        strcpy(name, n);
        priority = p;
        burstTime = b;
        remainingTime = b;
        arrivalTime = a;
        waitingTime = 0;
        turnaroundTime = 0;
        completionTime = 0;
        state = READY;
    }
};

struct ComparePriority {
    bool operator()(const PCB* a, const PCB* b) {
        return a->priority < b->priority;
    }
};

class Scheduler {
private:
    vector<PCB> processes;
    priority_queue<PCB*, vector<PCB*>, ComparePriority> readyQueue;
    PCB* runningProcess;
    vector<PCB> finishedQueue;
    int currentTime;
    int timeSlice;
    int priorityBase;

public:
    Scheduler() : runningProcess(NULL), currentTime(0), timeSlice(3), priorityBase(50) {}
    
    void setParameters(int ts, int pb) {
        timeSlice = ts;
        priorityBase = pb;
    }
    
    void addProcess(const char* name, int priority, int burstTime, int arrivalTime) {
        PCB pcb(name, priority, burstTime, arrivalTime);
        processes.push_back(pcb);
    }
    
    void generateRandomProcesses(int count) {
        processes.clear();
        char names[] = "ABCDEFGHIJ";
        
        for (int i = 0; i < count; i++) {
            int priority = rand() % 30 + 20;
            int burstTime = rand() % 10 + 3;
            int arrivalTime = rand() % 5;
            char name[2] = {names[i], '\0'};
            addProcess(name, priority, burstTime, arrivalTime);
        }
        
        cout << "\n=== Generated " << count << " processes ===" << endl;
        printProcessList();
    }
    
    void adjustPriority(PCB& pcb) {
        int waitBonus = pcb.waitingTime / 2;
        int newPriority = priorityBase - pcb.remainingTime + waitBonus;
        if (newPriority < 1) newPriority = 1;
        if (newPriority > 100) newPriority = 100;
        pcb.priority = newPriority;
    }
    
    void moveArrivedProcessesToReady() {
        for (int i = 0; i < processes.size(); i++) {
            PCB& p = processes[i];
            if (p.state == READY && p.arrivalTime <= currentTime && !isInReadyQueue(p.name)) {
                adjustPriority(p);
                readyQueue.push(&p);
                cout << "[Time " << currentTime << "] Process " << p.name 
                     << " arrived, priority: " << p.priority << endl;
            }
        }
    }
    
    bool isInReadyQueue(const char* name) {
        priority_queue<PCB*, vector<PCB*>, ComparePriority> temp = readyQueue;
        while (!temp.empty()) {
            if (strcmp(temp.top()->name, name) == 0) return true;
            temp.pop();
        }
        return false;
    }
    
    void selectNextProcess() {
        if (readyQueue.empty()) return;
        
        runningProcess = readyQueue.top();
        readyQueue.pop();
        runningProcess->state = RUNNING;
        cout << "[Time " << currentTime << "] Process " << runningProcess->name 
             << " starts running, priority: " << runningProcess->priority << endl;
    }
    
    void executeProcess() {
        if (!runningProcess) return;
        
        runningProcess->remainingTime--;
        currentTime++;
        
        updateWaitingTime();
        
        if (runningProcess->remainingTime == 0) {
            runningProcess->state = FINISHED;
            runningProcess->completionTime = currentTime;
            runningProcess->turnaroundTime = runningProcess->completionTime - runningProcess->arrivalTime;
            runningProcess->waitingTime = runningProcess->turnaroundTime - runningProcess->burstTime;
            finishedQueue.push_back(*runningProcess);
            
            cout << "[Time " << currentTime << "] Process " << runningProcess->name 
                 << " completed! Turnaround: " << runningProcess->turnaroundTime 
                 << ", Waiting: " << runningProcess->waitingTime << endl;
            runningProcess = NULL;
        } else if (runningProcess->remainingTime % timeSlice == 0) {
            runningProcess->state = READY;
            adjustPriority(*runningProcess);
            incrementReadyQueuePriority();
            readyQueue.push(runningProcess);
            
            cout << "[Time " << currentTime << "] Process " << runningProcess->name 
                 << " quantum expired, re-added to ready queue, priority: " << runningProcess->priority << endl;
            runningProcess = NULL;
        }
    }
    
    void updateWaitingTime() {
        vector<PCB*> temp;
        while (!readyQueue.empty()) {
            PCB* p = readyQueue.top();
            readyQueue.pop();
            p->waitingTime++;
            temp.push_back(p);
        }
        for (auto p : temp) readyQueue.push(p);
    }
    
    void incrementReadyQueuePriority() {
        vector<PCB*> temp;
        while (!readyQueue.empty()) {
            PCB* p = readyQueue.top();
            readyQueue.pop();
            if (p->priority < 100) p->priority++;
            temp.push_back(p);
        }
        for (auto p : temp) readyQueue.push(p);
    }
    
    void schedule() {
        cout << "\n===== Scheduling Started =====" << endl;
        
        while (finishedQueue.size() < processes.size()) {
            moveArrivedProcessesToReady();
            
            if (!runningProcess && readyQueue.empty()) {
                currentTime++;
                cout << "[Time " << currentTime << "] CPU idle" << endl;
                continue;
            }
            
            if (!runningProcess && !readyQueue.empty()) {
                selectNextProcess();
            }
            
            if (runningProcess) {
                executeProcess();
            }
        }
        
        cout << "\n===== All Processes Completed =====" << endl;
        printResults();
    }
    
    void printProcessList() {
        cout << left << setw(8) << "Name" 
             << setw(10) << "Priority" 
             << setw(10) << "BurstTime" 
             << setw(10) << "Arrival" << endl;
        cout << "-----------------------------------------" << endl;
        
        for (int i = 0; i < processes.size(); i++) {
            const PCB& p = processes[i];
            cout << left << setw(8) << p.name 
                 << setw(10) << p.priority 
                 << setw(10) << p.burstTime 
                 << setw(10) << p.arrivalTime << endl;
        }
        cout << endl;
    }
    
    void printResults() {
        cout << "\n===== Scheduling Results =====" << endl;
        cout << left << setw(8) << "Name" 
             << setw(10) << "Complete" 
             << setw(12) << "Turnaround" 
             << setw(12) << "Waiting" << endl;
        cout << "---------------------------------------------" << endl;
        
        int totalTurnaround = 0, totalWaiting = 0;
        for (int i = 0; i < finishedQueue.size(); i++) {
            const PCB& p = finishedQueue[i];
            cout << left << setw(8) << p.name 
                 << setw(10) << p.completionTime 
                 << setw(12) << p.turnaroundTime 
                 << setw(12) << p.waitingTime << endl;
            totalTurnaround += p.turnaroundTime;
            totalWaiting += p.waitingTime;
        }
        
        int n = finishedQueue.size();
        cout << "\nStatistics:" << endl;
        cout << "Total processes: " << n << endl;
        cout << "Average turnaround: " << fixed << setprecision(1) 
             << (double)totalTurnaround / n << endl;
        cout << "Average waiting: " << fixed << setprecision(1) 
             << (double)totalWaiting / n << endl;
    }
};

int main() {
    srand(time(NULL));
    
    Scheduler scheduler;
    int count, ts, pb;
    
    cout << "===== OS Experiment 1 - Process Scheduling =====" << endl;
    cout << "Dynamic Priority with Round Robin Scheduling" << endl << endl;
    
    cout << "Enter number of processes (1-10): ";
    cin >> count;
    count = count < 1 ? 1 : (count > 10 ? 10 : count);
    
    cout << "Enter time slice (1-10): ";
    cin >> ts;
    ts = ts < 1 ? 1 : (ts > 10 ? 10 : ts);
    
    cout << "Enter priority base (10-100): ";
    cin >> pb;
    pb = pb < 10 ? 10 : (pb > 100 ? 100 : pb);
    
    scheduler.setParameters(ts, pb);
    scheduler.generateRandomProcesses(count);
    
    cout << "\nPress Enter to start scheduling...";
    cin.get();
    cin.get();
    
    scheduler.schedule();
    
    cout << "\nPress Enter to exit...";
    cin.get();
    
    return 0;
}