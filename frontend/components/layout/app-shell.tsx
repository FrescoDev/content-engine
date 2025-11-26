"use client"

import type { ReactNode } from "react"
import { cn } from "@/lib/utils"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutDashboard, FileText, Shield, History, BarChart3, Sparkles, Menu, X, Settings } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"

interface AppShellProps {
  children: ReactNode
}

const navigation = [
  { name: "Today", href: "/today", icon: LayoutDashboard },
  { name: "Scripts", href: "/scripts", icon: FileText },
  { name: "Integrity", href: "/integrity", icon: Shield },
  { name: "History", href: "/history", icon: History },
  { name: "Performance", href: "/performance", icon: BarChart3 },
  { name: "Admin", href: "/admin", icon: Settings },
]

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="flex h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-56 border-r border-border bg-sidebar flex-col">
        <div className="p-4 border-b border-sidebar-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-sidebar-foreground">Content Engine</h1>
              <p className="text-xs text-muted-foreground">AI Production Console</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-foreground font-medium"
                    : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground",
                )}
              >
                <item.icon className="w-4 h-4" />
                {item.name}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-sidebar-border">
          <div className="text-xs text-muted-foreground">
            <div className="flex items-center justify-between mb-1">
              <span>System Status</span>
              <span className="inline-flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-success" />
                Active
              </span>
            </div>
          </div>
        </div>
      </aside>

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)} />
          <aside className="fixed left-0 top-0 bottom-0 w-full max-w-[280px] border-r border-border bg-sidebar flex flex-col shadow-xl animate-in slide-in-from-left duration-200">
            <div className="p-4 border-b border-sidebar-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-primary-foreground" />
                </div>
                <div>
                  <h1 className="text-sm font-semibold text-sidebar-foreground">Content Engine</h1>
                  <p className="text-xs text-muted-foreground">AI Production Console</p>
                </div>
              </div>
              <Button size="icon" variant="ghost" onClick={() => setMobileMenuOpen(false)} className="h-8 w-8">
                <X className="w-4 h-4" />
              </Button>
            </div>

            <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
              {navigation.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors",
                      isActive
                        ? "bg-sidebar-accent text-sidebar-foreground font-medium"
                        : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground",
                    )}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>

            <div className="p-4 border-t border-sidebar-border">
              <div className="text-xs text-muted-foreground">
                <div className="flex items-center justify-between mb-1">
                  <span>System Status</span>
                  <span className="inline-flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-success" />
                    Active
                  </span>
                </div>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 overflow-auto flex flex-col">
        <div className="lg:hidden sticky top-0 z-40 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80 px-4 py-3 flex items-center justify-between">
          <Button size="icon" variant="ghost" onClick={() => setMobileMenuOpen(true)} className="h-9 w-9">
            <Menu className="w-5 h-5" />
          </Button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-primary flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold">Content Engine</span>
          </div>
          <div className="w-9" />
        </div>
        {children}
      </main>
    </div>
  )
}
