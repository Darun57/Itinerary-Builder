import * as React from "react"
import { ChevronsUpDown } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Checkbox } from "@/components/ui/checkbox"

export function MultiSelect({
  options,
  selected,
  onChange,
  placeholder = "Select options",
}: {
  options: { label: string; value: string }[]
  selected: string[]
  onChange: (values: string[]) => void
  placeholder?: string
}) {
  const [open, setOpen] = React.useState(false)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        className={cn(
          "inline-flex items-center justify-between whitespace-nowrap rounded-lg border border-input bg-background/50 px-3 py-2 text-sm font-normal transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50 w-full h-auto min-h-10 text-left hover:bg-muted hover:text-foreground"
        )}
      >
        <div className="flex flex-wrap gap-1 items-center overflow-hidden">
            {selected.length > 0 ? (
              selected.join(", ")
            ) : (
              <span className="text-muted-foreground">{placeholder}</span>
            )}
          </div>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </PopoverTrigger>
      <PopoverContent 
        className="w-[var(--radix-popover-trigger-width)] p-1" 
        align="start"
      >
        <div className="max-h-64 overflow-y-auto">
          {options.map((option) => {
            const isSelected = selected.includes(option.value);
            return (
              <div
                key={option.value}
                className="flex items-center space-x-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground cursor-pointer"
                onClick={() => {
                  if (isSelected) {
                    onChange(selected.filter((item) => item !== option.value))
                  } else {
                    onChange([...selected, option.value])
                  }
                }}
              >
                <Checkbox 
                  checked={isSelected}
                  className="pointer-events-none" 
                />
                <span>{option.label}</span>
              </div>
            )
          })}
        </div>
      </PopoverContent>
    </Popover>
  )
}
