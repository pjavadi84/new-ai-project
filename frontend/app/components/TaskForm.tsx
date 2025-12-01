'use client';

import { useState } from "react";
import { Task } from "@/types";
import { API_URL } from "@/app/lib/api";

interface TaskFormProps {
    onTaskCreated: (newTask: Task) => void;
}

export default function TaskForm({ onTaskCreated }: TaskFormProps){
    const [title, setTitle] = useState('');

    const handleSubmit =   async(e: React.FormEvent) => {
        e.preventDefault();
        if (!title.trim()) return;

        try{
            // Send the POST request:
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'content-type':'application/json'
                },
                // 2. Data is sent as a JSON string in the body
                body: JSON.stringify({title: title})
            });

            console.log('response is:', response);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // 3. Django sends the full new Task object back, including the ID
            const newTask: Task = await response.json();

            // 4. Call the function passed down from the parent to update the list
            onTaskCreated(newTask);

            setTitle('');

        }catch(error){
            console.log('Error creating task:', error);
            alert("Failed to create the task. check the console");
        }
    }

    return (
    // Apply Tailwind classes for styling the form
    <form onSubmit={handleSubmit} className="mt-8 mb-6 p-4 border rounded-lg bg-indigo-50 shadow-md">
      <input
        type="text"
        placeholder="Enter new task title..."
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="w-full p-3 border border-indigo-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-gray-700"
      />
      <button
        type="submit"
        className="mt-3 w-full bg-indigo-600 text-white p-3 rounded-md font-semibold hover:bg-indigo-700 transition duration-150 disabled:bg-indigo-400"
        disabled={!title.trim()}
      >
        Add Task
      </button>
    </form>
  );
}
