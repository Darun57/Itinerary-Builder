"use client";
import React, { useEffect, useState, useCallback } from "react";
import type { Task, Staff } from "../../types";
import { fetchTasks, updateTask, deleteTask, createTask, fetchStaff } from "../../api";

const PRIORITY_COLORS: Record<string, string> = { low: "#9db4e8", medium: "#D4AF37", high: "#e87878" };

export function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDone, setShowDone] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [newTask, setNewTask] = useState({ title: "", priority: "medium", due_date: "", assigned_staff_id: "" });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [t, s] = await Promise.all([fetchTasks(showDone ? undefined : false), fetchStaff()]);
      setTasks(t as Task[]);
      setStaffList(s);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }, [showDone]);

  useEffect(() => { load(); }, [load]);

  const toggleDone = async (task: Task) => {
    await updateTask(task.id, { is_done: !task.is_done });
    load();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this task?")) return;
    await deleteTask(id);
    load();
  };

  const handleCreate = async () => {
    if (!newTask.title.trim()) return;
    await createTask({
      ...newTask,
      assigned_staff_id: newTask.assigned_staff_id ? parseInt(newTask.assigned_staff_id) : undefined,
    } as any);
    setNewTask({ title: "", priority: "medium", due_date: "", assigned_staff_id: "" });
    setShowForm(false);
    load();
  };

  return (
    <div className="crm-page">
      <div className="crm-page-header">
        <div>
          <h2 className="crm-page-title"><i className="ti ti-checks" /> Tasks & Follow-ups</h2>
          <p className="crm-page-sub">{tasks.filter(t => !t.is_done).length} pending tasks</p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button className="crm-btn-ghost" onClick={() => setShowDone(v => !v)}>
            {showDone ? "Hide Completed" : "Show Completed"}
          </button>
          <button className="btn-gold" onClick={() => setShowForm(v => !v)}>
            <i className="ti ti-plus" /> Add Task
          </button>
        </div>
      </div>

      {showForm && (
        <div className="crm-quick-form">
          <input className="crm-input" placeholder="Task title..." value={newTask.title} onChange={e => setNewTask(p => ({ ...p, title: e.target.value }))} />
          <select className="crm-input" value={newTask.priority} onChange={e => setNewTask(p => ({ ...p, priority: e.target.value }))}>
            {["low","medium","high"].map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase()+p.slice(1)}</option>)}
          </select>
          <input className="crm-input" type="date" value={newTask.due_date} onChange={e => setNewTask(p => ({ ...p, due_date: e.target.value }))} />
          <select className="crm-input" value={newTask.assigned_staff_id} onChange={e => setNewTask(p => ({ ...p, assigned_staff_id: e.target.value }))}>
            <option value="">Assign to...</option>
            {staffList.map(s => <option key={s.id} value={s.id}>{s.full_name}</option>)}
          </select>
          <button className="btn-gold" onClick={handleCreate}><i className="ti ti-check" /> Save</button>
        </div>
      )}

      {loading ? (
        <div className="crm-loading"><i className="ti ti-loader-2 crm-spin" /> Loading tasks...</div>
      ) : tasks.length === 0 ? (
        <div className="crm-empty"><i className="ti ti-checks" /><p>No tasks. All clear!</p></div>
      ) : (
        <div className="crm-task-list">
          {tasks.map(task => (
            <div key={task.id} className={`crm-task-item${task.is_done ? " crm-task-done" : ""}`}>
              <button className="crm-task-check" onClick={() => toggleDone(task)}>
                <i className={`ti ${task.is_done ? "ti-circle-check-filled" : "ti-circle"}`} style={{ color: task.is_done ? "#3FBF7F" : "#555" }} />
              </button>
              <div className="crm-task-body">
                <div className="crm-task-title">{task.title}</div>
                {task.description && <div className="crm-task-desc">{task.description}</div>}
                <div className="crm-task-meta">
                  <span className="crm-chip" style={{ color: PRIORITY_COLORS[task.priority], borderColor: PRIORITY_COLORS[task.priority] + "44" }}>
                    {task.priority}
                  </span>
                  {task.due_date && <span><i className="ti ti-calendar" /> {task.due_date}</span>}
                  {task.assigned_staff && <span><i className="ti ti-user" /> {task.assigned_staff.full_name}</span>}
                </div>
              </div>
              <button className="crm-btn-icon crm-btn-danger" onClick={() => handleDelete(task.id)}><i className="ti ti-trash" /></button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
