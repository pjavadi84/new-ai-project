'use client';

import { Task } from '@/types';
import { API_URL } from '@/app/lib/api';

interface TaskItemProps {
    task: Task;
    onTaskUpdate: (updatedTask: Task) => void;
    onTaskDelete: (taskId: number) => void;
}

export default function TaskItem({task, onTaskUpdate, onTaskDelete}: TaskItemProps){
    // We will fill the logic here for Update and Delete
    const handleToggle = async () =>{
        // 1. Create the inverse (new) status
        const newCompletedStatus = !task.completed;

        try{
            // 2. Send the PATCH request to the specific task URL
            const response = await fetch(`${API_URL}${task.id}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                // 3. Send ONLY the field we want to update
                body: JSON.stringify({ completed: newCompletedStatus }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

                // 4. Django returns the updated task object
            const updatedTask: Task = await response.json();
            
            // 5. Tell the parent component (page.tsx) to update its list
            onTaskUpdate(updatedTask);
        } catch(error){
            console.error('Error in toggling the update', Error);
            alert('Failed to update task.');
        }
    }


   
    const handleTaskDelete = async () => {
        try {
            const response = await fetch(`${API_URL}${task.id}/`, { method: 'DELETE' });

            if (!response.ok && response.status !== 204) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            onTaskDelete(task.id);
        } catch (error) {
            console.error('Error deleting task:', error);
            alert('Failed to delete task.');
        }
    };
    
    // Helper to determine text styling
    const itemClasses = `p-3 border rounded-lg flex justify-between items-center transition duration-150 ease-in-out shadow-sm 
                        ${task.completed ? 'bg-green-100 border-green-300 text-gray-500 line-through' : 'bg-gray-50 hover:bg-gray-100'}`;

    return (
        <li className={itemClasses}>
            
            {/* 1. Checkbox for Toggling (Update operation) */}
            <div className="flex items-center space-x-3">
                <input
                    type="checkbox"
                    checked={task.completed}
                    onChange={handleToggle}
                    className="h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <span className="text-lg">{task.title}</span>
            </div>

            {/* 2. Delete Button (Delete operation) */}
            <button
                onClick={handleTaskDelete}
                className="text-sm text-red-600 hover:text-red-800 font-semibold transition-colors"
            >
                Delete
            </button>
        </li>
    );

    
}
