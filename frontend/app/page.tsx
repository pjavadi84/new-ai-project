"use client"

import Image from "next/image";
import { Task } from '@/types';
import TaskForm from "./components/TaskForm";
import { useEffect, useState } from "react";
import TaskItem from './components/TaskItem';
import { API_URL } from "@/app/lib/api";

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Function passed to the form to update the list after a successful POST
  const handleTaskCreated = (newTask: Task)=>{
    setTasks(prevTasks => [newTask, ...prevTasks])
  }

  useEffect(()=>{
    async function fetchTasks(){
      try{
        const response = await fetch(API_URL);

        if(!response.ok){
          throw new Error(`HTTP error: ${response.status}`)
        }

        const data: Task[] = await response.json();
        setTasks(data);
      } catch {
        console.error("Could not fetch tasks:", Error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchTasks();
  }, []);


  // --- RENDERING ---

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen bg-gray-50">
        <p className="text-xl text-gray-700">Loading tasks...</p>
      </div>
    );
  }

  // --- UPDATE (PATCH) HANDLER: Immutably update ONE item ---
  const handleTaskUpdated = (updatedTask: Task) => {
      // 1. Map over the existing tasks.
      // 2. If the current task ID matches the updated ID, replace it with the new object.
      // 3. Otherwise, keep the old task object.
      setTasks(prevTasks =>
          prevTasks.map(task => 
              task.id === updatedTask.id ? updatedTask : task
          )
      );
  };

  const handleTaskDeleted = (taskId: number) => {
    setTasks(prevTasks => prevTasks.filter(task => task.id !==taskId));
  }


  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        {/* TaskForm handles the POST request */}
        <TaskForm onTaskCreated={handleTaskCreated} />

        <h1 className="text-3xl font-bold mb-6 text-gray-800 border-b pb-2">
          TypeScript Task Manager
        </h1>

        <h2 className="text-xl font-semibold mb-4 text-gray-600">Tasks List:</h2>

        {tasks.length > 0 ? (
          <ul className="space-y-3">
            {tasks.map(task => (
              <TaskItem 
                key={task.id}
                task={task}
                onTaskUpdate={handleTaskUpdated} // Pass the handler down
                onTaskDelete={handleTaskDeleted}             
          />
          ))}
        </ul>
      ) : (
        <p className="text-gray-500 italic">No tasks found. Create one using the form above!</p>
      )}
      </main>
    </div>
  );
}
