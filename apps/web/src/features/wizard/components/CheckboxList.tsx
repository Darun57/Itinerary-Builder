"use client";

import React from "react";
import { useFormContext } from "react-hook-form";
import { TripRequestType } from "../schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Checkbox } from "@/components/ui/checkbox";

interface CheckboxListProps {
  /** The react-hook-form field name (must be a string array field). */
  name: keyof TripRequestType;
  /** The options to display. */
  items: string[];
}

/**
 * Renders a list of labelled checkboxes bound to a react-hook-form array field.
 * Replaces the repeated 30-line checkbox-list pattern across multiple steps.
 */
export function CheckboxList({ name, items }: CheckboxListProps) {
  const { control } = useFormContext<TripRequestType>();

  return (
    <FormField
      control={control}
      name={name}
      render={() => (
        <FormItem>
          <div className="flex flex-wrap gap-4">
            {items.map((item) => (
              <FormField
                key={item}
                control={control}
                name={name}
                render={({ field }) => (
                  <FormItem key={item} className="flex flex-row items-center space-x-2 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={(field.value as string[])?.includes(item)}
                        onCheckedChange={(checked) =>
                          checked
                            ? field.onChange([...((field.value as string[]) || []), item])
                            : field.onChange(((field.value as string[]) || []).filter((v) => v !== item))
                        }
                      />
                    </FormControl>
                    <FormLabel className="font-normal cursor-pointer">{item}</FormLabel>
                  </FormItem>
                )}
              />
            ))}
          </div>
          <FormMessage />
        </FormItem>
      )}
    />
  );
}
