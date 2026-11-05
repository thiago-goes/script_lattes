CREATE TABLE `production_review_history` (
	`product_id` text NOT NULL,
	`revision` integer NOT NULL,
	`payload` text NOT NULL,
	`created_at` text NOT NULL,
	`actor` text NOT NULL,
	PRIMARY KEY(`product_id`, `revision`)
);
--> statement-breakpoint
CREATE TABLE `production_reviews` (
	`product_id` text PRIMARY KEY NOT NULL,
	`action` text NOT NULL,
	`category` text NOT NULL,
	`kind` text NOT NULL,
	`notes` text NOT NULL,
	`evidence` text NOT NULL,
	`source_signature` text NOT NULL,
	`source_snapshot` text NOT NULL,
	`revision` integer NOT NULL,
	`updated_at` text NOT NULL,
	`actor` text NOT NULL,
	`event_id` text NOT NULL
);
