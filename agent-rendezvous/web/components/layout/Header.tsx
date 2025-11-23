'use client';

import * as React from 'react';
import { Link01Icon } from 'hugeicons-react';
import { motion } from 'framer-motion';

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-background/60 backdrop-blur-xl supports-[backdrop-filter]:bg-background/30">
      <div className="container mx-auto flex h-14 items-center justify-between px-4 md:px-6 lg:px-8 max-w-6xl">
        <motion.div
          className="flex items-center gap-2"
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 border border-white/10">
             <Link01Icon className="h-4 w-4 text-foreground" />
          </div>
          <h1 className="font-serif text-xl font-medium tracking-tight text-foreground">
            AgentBridge
          </h1>
        </motion.div>
        
        <nav className="flex items-center gap-6 text-sm font-medium text-muted-foreground">
          <LinkItem href="#" label="Marketplace" delay={0.1} />
          <LinkItem href="#" label="Agents" delay={0.2} />
          <LinkItem href="#" label="History" delay={0.3} />
        </nav>
      </div>
    </header>
  );
}

function LinkItem({ href, label, delay }: { href: string; label: string; delay: number }) {
  return (
    <motion.a 
      href={href}
      className="hover:text-foreground transition-colors"
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
    >
      {label}
    </motion.a>
  )
}
