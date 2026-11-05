import { sqliteTable,text,integer,primaryKey } from 'drizzle-orm/sqlite-core';
export const reviews=sqliteTable('production_reviews',{
 productId:text('product_id').primaryKey(),action:text('action').notNull(),category:text('category').notNull(),kind:text('kind').notNull(),notes:text('notes').notNull(),evidence:text('evidence').notNull(),sourceSignature:text('source_signature').notNull(),sourceSnapshot:text('source_snapshot').notNull(),revision:integer('revision').notNull(),updatedAt:text('updated_at').notNull(),actor:text('actor').notNull(),eventId:text('event_id').notNull()
});
export const history=sqliteTable('production_review_history',{
 productId:text('product_id').notNull(),revision:integer('revision').notNull(),payload:text('payload').notNull(),createdAt:text('created_at').notNull(),actor:text('actor').notNull()
},t=>[primaryKey({columns:[t.productId,t.revision]})]);
