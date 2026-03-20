"use client";

import { useAuth } from "@/hooks/use-auth";
import { Avatar } from "@/components/ui/avatar";
import { DropdownMenu, DropdownItem, DropdownSeparator } from "@/components/ui/dropdown-menu";
import { useUiStore } from "@/stores/ui-store";

export function Topbar() {
  const { user, logout } = useAuth();
  const { toggleMobileSidebar } = useUiStore();

  const fullName = user ? `${user.first_name} ${user.last_name}` : "User";

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200/80 bg-white/95 px-4 backdrop-blur-sm lg:px-6">
      {/* Left: mobile menu + search */}
      <div className="flex items-center gap-3">
        <button
          onClick={toggleMobileSidebar}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
          </svg>
        </button>

        <div className="hidden md:block">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <input
              type="text"
              placeholder="Search transactions, entities, alerts..."
              className="w-80 rounded-lg border border-slate-200 bg-slate-50/80 py-2 pl-10 pr-4 text-sm placeholder:text-slate-400 focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20"
            />
          </div>
        </div>
      </div>

      {/* Right: notifications + user menu */}
      <div className="flex items-center gap-2">
        {/* Notifications bell */}
        <button className="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
          </svg>
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-danger-500" />
        </button>

        {/* User dropdown */}
        <DropdownMenu
          trigger={
            <button className="flex items-center gap-2 rounded-lg p-1.5 transition-colors hover:bg-slate-100">
              <Avatar name={fullName} size="sm" />
              <div className="hidden text-left md:block">
                <p className="text-sm font-medium text-slate-900">{fullName}</p>
                <p className="text-xs capitalize text-slate-500">{user?.role}</p>
              </div>
              <svg className="hidden h-4 w-4 text-slate-400 md:block" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
          }
        >
          <div className="px-3 py-2 text-sm md:hidden">
            <p className="font-medium text-slate-900">{fullName}</p>
            <p className="capitalize text-slate-500">{user?.role}</p>
          </div>
          <DropdownSeparator />
          <DropdownItem onClick={() => {}}>Profile</DropdownItem>
          <DropdownItem onClick={() => {}}>Settings</DropdownItem>
          <DropdownSeparator />
          <DropdownItem onClick={logout} destructive>
            Sign out
          </DropdownItem>
        </DropdownMenu>
      </div>
    </header>
  );
}
