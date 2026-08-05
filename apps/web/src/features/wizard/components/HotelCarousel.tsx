"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { FormField, FormItem, FormLabel, FormControl, FormDescription } from "@/components/ui/form";
import { useFormContext } from "react-hook-form";
import { TripRequestType } from "../../schema";

interface Hotel {
  hotel_id?: string;
  hotel_name: string;
  location?: string;
  category?: string;
  nightly_price?: number | string;
  description?: string;
}

interface HotelCarouselProps {
  hotels: Hotel[];
  location: string;
}

// Breakpoint → cards visible
function useCardsPerView(containerRef: React.RefObject<HTMLDivElement | null>): number {
  const [count, setCount] = useState(3);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      if (w < 480) setCount(1);
      else if (w < 768) setCount(2);
      else if (w < 1100) setCount(3);
      else setCount(4);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [containerRef]);

  return count;
}

export function HotelCarousel({ hotels, location }: HotelCarouselProps) {
  const { control } = useFormContext<TripRequestType>();

  const containerRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const cardsPerView = useCardsPerView(containerRef);

  const [index, setIndex] = useState(0); // leftmost visible card index
  const [isDragging, setIsDragging] = useState(false);
  const [dragStartX, setDragStartX] = useState(0);
  const [dragDeltaX, setDragDeltaX] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  const maxIndex = Math.max(0, hotels.length - cardsPerView);
  const canPrev = index > 0;
  const canNext = index < maxIndex;

  // Card width as percentage of container
  const cardWidthPct = 100 / cardsPerView;

  const slideTo = useCallback((newIndex: number) => {
    if (isAnimating) return;
    const clamped = Math.max(0, Math.min(newIndex, maxIndex));
    setIndex(clamped);
    setIsAnimating(true);
    setTimeout(() => setIsAnimating(false), 400);
  }, [isAnimating, maxIndex]);

  const handlePrev = () => slideTo(index - Math.min(cardsPerView, 3));
  const handleNext = () => slideTo(index + Math.min(cardsPerView, 3));

  // Keyboard navigation
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") handlePrev();
      if (e.key === "ArrowRight") handleNext();
    };
    el.addEventListener("keydown", onKey);
    return () => el.removeEventListener("keydown", onKey);
  }, [index, cardsPerView, maxIndex]);

  // Pointer drag
  const onPointerDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStartX(e.clientX);
    setDragDeltaX(0);
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    setDragDeltaX(e.clientX - dragStartX);
  };

  const onPointerUp = (e: React.PointerEvent) => {
    if (!isDragging) return;
    setIsDragging(false);
    const threshold = (containerRef.current?.offsetWidth ?? 300) * 0.2;
    if (dragDeltaX < -threshold) slideTo(index + 1);
    else if (dragDeltaX > threshold) slideTo(index - 1);
    setDragDeltaX(0);
  };

  // Touch swipe
  const touchStartX = useRef(0);
  const onTouchStart = (e: React.TouchEvent) => { touchStartX.current = e.touches[0].clientX; };
  const onTouchEnd = (e: React.TouchEvent) => {
    const delta = e.changedTouches[0].clientX - touchStartX.current;
    const threshold = (containerRef.current?.offsetWidth ?? 300) * 0.2;
    if (delta < -threshold) slideTo(index + 1);
    else if (delta > threshold) slideTo(index - 1);
  };

  // translateX: base shift + live drag offset
  const containerWidth = containerRef.current?.offsetWidth ?? 0;
  const cardWidthPx = containerWidth / cardsPerView;
  const baseTranslate = -index * cardWidthPx;
  const liveTranslate = isDragging ? baseTranslate + dragDeltaX : baseTranslate;

  return (
    <div className="space-y-3">
      {/* Header row */}
      <div className="flex items-center justify-between px-1">
        <h4 className="text-md font-semibold text-primary/80">{location}</h4>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground mr-2 tabular-nums">
            {Math.min(index + cardsPerView, hotels.length)}/{hotels.length}
          </span>
          <button
            type="button"
            onClick={handlePrev}
            disabled={!canPrev}
            aria-label="Previous hotels"
            className={`p-1.5 rounded-full border transition-all duration-200 cursor-pointer
              ${canPrev
                ? "bg-background hover:bg-muted border-border hover:border-primary/40 hover:shadow-sm"
                : "bg-background/30 border-border/30 opacity-30 cursor-not-allowed"
              }`}
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={handleNext}
            disabled={!canNext}
            aria-label="Next hotels"
            className={`p-1.5 rounded-full border transition-all duration-200 cursor-pointer
              ${canNext
                ? "bg-background hover:bg-muted border-border hover:border-primary/40 hover:shadow-sm"
                : "bg-background/30 border-border/30 opacity-30 cursor-not-allowed"
              }`}
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Carousel viewport — overflow hidden so cards don't spill */}
      <div
        ref={containerRef}
        className="overflow-hidden w-full select-none"
        tabIndex={0}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
        style={{ cursor: isDragging ? "grabbing" : "grab" }}
      >
        {/* Sliding track */}
        <div
          ref={trackRef}
          className="flex"
          style={{
            transform: `translateX(${liveTranslate}px)`,
            transition: isDragging ? "none" : "transform 0.38s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
            willChange: "transform",
          }}
        >
          {hotels.map((hotel) => (
            <div
              key={hotel.hotel_id || hotel.hotel_name}
              style={{ minWidth: `${cardWidthPct}%`, maxWidth: `${cardWidthPct}%` }}
              className="px-2 box-border"
            >
              <FormField
                control={control}
                name="selected_hotels"
                render={({ field }) => {
                  const isChecked = Array.isArray(field.value) && field.value.includes(hotel.hotel_name);
                  return (
                    <FormItem
                      className={`h-full flex flex-row items-start gap-3 rounded-xl border p-4 bg-background/50 
                        transition-all duration-200
                        ${isChecked
                          ? "border-primary/60 bg-primary/5 shadow-sm shadow-primary/10"
                          : "border-border hover:border-primary/30 hover:shadow-sm"
                        }`}
                    >
                      <FormControl>
                        <Checkbox
                          checked={isChecked}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              field.onChange([...(field.value || []), hotel.hotel_name]);
                            } else {
                              field.onChange((field.value || []).filter((v: string) => v !== hotel.hotel_name));
                            }
                          }}
                        />
                      </FormControl>
                      <div className="space-y-1 leading-none w-full min-w-0">
                        <FormLabel
                          className={`font-semibold cursor-pointer block truncate text-sm mb-1.5 
                            ${isChecked ? "text-primary" : "text-foreground"}`}
                        >
                          {hotel.hotel_name}
                        </FormLabel>
                        <FormDescription className="text-xs line-clamp-3 leading-relaxed">
                          {hotel.description}
                        </FormDescription>
                        <div className="pt-2 mt-2 border-t border-border/50 text-xs text-muted-foreground flex justify-between items-center">
                          <span>{hotel.category}</span>
                          <span className={`font-semibold ${isChecked ? "text-primary" : "text-foreground"}`}>
                            ₹{hotel.nightly_price?.toLocaleString?.() ?? hotel.nightly_price}
                          </span>
                        </div>
                      </div>
                    </FormItem>
                  );
                }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Dot indicators */}
      {hotels.length > cardsPerView && (
        <div className="flex justify-center gap-1.5 pt-1">
          {Array.from({ length: maxIndex + 1 }).map((_, i) => (
            <button
              key={i}
              type="button"
              onClick={() => slideTo(i)}
              aria-label={`Go to position ${i + 1}`}
              className={`rounded-full transition-all duration-200 cursor-pointer
                ${i === index
                  ? "bg-primary w-5 h-1.5"
                  : "bg-border hover:bg-primary/40 w-1.5 h-1.5"
                }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
