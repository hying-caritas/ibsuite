/*
 * pi_page_parse.c
 *
 * Copyright 2008-2009 Huang Ying <huang.ying.caritas@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 */

#include <stdarg.h>
#include <libgen.h>
#include <unistd.h>
#include <assert.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include <pgm.h>

#include "list.h"

struct pi_rect {
	int left;
	int top;
	int right;
	int bottom;
};

struct pi_image {
	gray maxval;
	int width;
	int height;
	gray **pxls;
};

struct pi_char {
	int left;
	int right;
	struct list_head list;
};

struct pi_page;
struct pi_line {
	struct pi_rect bbox;
	struct list_head list;
	struct pi_page *page;
	struct list_head chars;
};

struct pi_page {
	struct pi_image *img;
	struct pi_rect bbox;
	struct list_head lines;
};

#define error_exit(ec, fmt...)			\
	do {					\
		fprintf(stderr, fmt);		\
		fprintf(stderr, "\n");		\
		assert(0);			\
		exit(ec);			\
	} while (0)

#define error_exit_on(cond, ec, fmt...)		\
	do {					\
		if (cond)			\
			error_exit(ec, fmt);	\
	} while (0)

#define error_exit_errno(ec, fmt...)				\
	do {							\
		fprintf(stderr, fmt);				\
		fprintf(stderr, ": %s.\n", strerror(errno));	\
		assert(0);					\
		exit(ec);					\
	} while (0)

#define error_exit_errno_on(cond, ec, fmt...)		\
	do {						\
		if (cond)				\
			error_exit_errno(ec, fmt);	\
	} while (0)

#ifndef max
static inline int max(int a, int b)
{
	return a > b ? a : b;
}
#endif

#ifndef min
static inline int min(int a, int b)
{
	return a < b ? a : b;
}
#endif

static float empty_coeff = 0.95;

struct pi_image *pi_image_load(const char *file_name)
{
	FILE *fin;
	struct pi_image *img;

	img = malloc(sizeof(struct pi_image));
	error_exit_on(!img, -1, "Error alloc memory for pi_image.");
	fin = fopen(file_name, "rb");
	error_exit_errno_on(!fin, -1, "Error open pgm image file %s",
			    file_name);
	img->pxls = pgm_readpgm(fin, &img->width, &img->height, &img->maxval);
	error_exit_on(!img->pxls, -1, "Error read pgm imge file %s", file_name);
	fclose(fin);

	return img;
}

void pi_image_free(struct pi_image *img)
{
	pgm_freearray(img->pxls, img->height);
	free(img);
}

static inline gray pi_image_get_pxl(struct pi_image *img,
				    int x, int y)
{
	return img->pxls[y][x];
}

static inline void pi_image_set_pxl(struct pi_image *img,
				    int x, int y,
				    gray val)
{
	img->pxls[y][x] = val;
}

static inline int pi_image_row_find_nonempty(struct pi_image *img,
					     int y, int sx, int ex,
					     gray empty)
{
	int x;
	gray *r = img->pxls[y];

	for (x = sx; x < ex; x++) {
		if (r[x] < empty)
			return x;
	}
	return ex;
}

static inline int pi_image_row_rfind_nonempty(struct pi_image *img,
					     int y, int sx, int ex,
					     gray empty)
{
	int x;
	gray *r = img->pxls[y];

	for (x = sx; x > ex; x--) {
		if (r[x] < empty)
			return x;
	}
	return ex;
}

static inline int pi_image_col_find_nonempty(struct pi_image *img,
					     int x, int sy, int ey,
					     gray empty)
{
	int y;
	gray **pxls = img->pxls;

	for (y = sy; y < ey; y++) {
		if (pxls[y][x] < empty)
			return y;
	}
	return ey;
}

void pi_image_get_bbox(struct pi_image *img,
		       struct pi_rect *bbox,
		       gray empty)
{
	int x, y, yt;
	int iw = img->width, ih = img->height;

	for (y = 0; y < ih; y++) {
		if (pi_image_row_find_nonempty(img, y, 0, iw, empty) != iw)
			break;
	}
	if (y == ih) {
		memset(bbox, 0, sizeof(*bbox));
		return;
	}
	bbox->top = yt = y;
	for (y = ih - 1; y >= 0; y--) {
		if (pi_image_row_find_nonempty(img, y, 0, iw, empty) != iw)
			break;
	}
	y++;
	bbox->bottom = y;
	for (x = 0; x < iw; x++) {
		if (pi_image_col_find_nonempty(img, x, yt, y, empty) != y)
			break;
	}
	bbox->left = x;
	for (x = iw - 1; x >= 0; x--) {
		if (pi_image_col_find_nonempty(img, x, yt, y, empty) != y)
			break;
	}
	bbox->right = x + 1;
}

struct pi_char *pi_char_new(int left, int right)
{
	struct pi_char *ch;

	ch = malloc(sizeof(struct pi_char));
	error_exit_on(!ch, -1, "Error alloc memory for pi_line.");
	ch->left = left;
	ch->right = right;

	return ch;
}

void pi_char_free(struct pi_char *ch)
{
	free(ch);
}

void pi_chars_free(struct list_head *chars)
{
	struct pi_char *c, *n;

	list_for_each_entry_safe(c, n, chars, list) {
		list_del(&c->list);
		pi_char_free(c);
	}
}

#define pi_line_for_each_char(ch, line)	\
	list_for_each_entry(ch, &line->chars, list)

static inline void pi_line_append_char(struct pi_line *line,
				       struct pi_char *ch)
{
	list_add_tail(&ch->list, &line->chars);
}

#define LS_IN_CHAR		0
#define LS_BETWEEN_CHAR		1

int pi_line_parse(struct pi_line *line)
{
	struct pi_char *ch;
	struct pi_image *img = line->page->img;
	struct pi_rect *lbox = &line->bbox;
	int iw = img->width;
	int cb, ce, x, y, sy, ey;
	gray empty = img->maxval * empty_coeff;
	int state = LS_IN_CHAR;

	sy = lbox->top;
	ey = lbox->bottom;
	cb = lbox->left;
	ce = cb - 1;
	for (x = lbox->left + 1; x < iw; x++) {
		y = pi_image_col_find_nonempty(img, x, sy, ey, empty);
		if (state == LS_IN_CHAR) {
			if (y == ey) {
				ce = x;
				ch = pi_char_new(cb, ce);
				pi_line_append_char(line, ch);
				state = LS_BETWEEN_CHAR;
			}
		} else {
			if (y != ey) {
				cb = x;
				state = LS_IN_CHAR;
			}
		}
	}

	if (ce < cb) {
		ce = x;
		ch = pi_char_new(cb, ce);
		pi_line_append_char(line, ch);
	}

	return ce;
}

struct pi_line *pi_line_new(struct pi_page *page,
			    int left, int top, int bottom)
{
	struct pi_line *line;

	line = malloc(sizeof(struct pi_line));
	error_exit_on(!line, -1, "Error alloc memory for pi_line.");
	line->page = page;
	line->bbox.left = left;
	line->bbox.top = top;
	line->bbox.bottom = bottom;
	INIT_LIST_HEAD(&line->chars);
	line->bbox.right = pi_line_parse(line);

	return line;
}

void pi_line_free(struct pi_line *line)
{
	pi_chars_free(&line->chars);
	free(line);
}

void pi_lines_free(struct list_head *lines)
{
	struct pi_line *l, *n;

	list_for_each_entry_safe(l, n, lines, list) {
		list_del(&l->list);
		pi_line_free(l);
	}
}

#define pi_page_for_each_line(line, page)	\
	list_for_each_entry(line, &page->lines, list)

void pi_page_append_line(struct pi_page *page,
			 struct pi_line *line)
{
	list_add_tail(&line->list, &page->lines);
}

#define PS_TOP_MARGIN		0
#define PS_IN_LINE		1
#define PS_BETWEEN_LINE		2

void pi_page_parse(struct pi_page *page)
{
	struct pi_line *line;
	struct pi_image *img = page->img;
	int iw = img->width, ih = img->height;
	int x, y;
	gray empty = img->maxval * empty_coeff;
	int pg_lft = 0, pg_rt = 0, pg_top = 0, pg_btm = 0;
	int ln_lft, ln_rt, ln_top, ln_btm;
	int state = PS_TOP_MARGIN;

	for (y = 0; y < ih; y++) {
		x = pi_image_row_find_nonempty(img, y, 0, iw, empty);
		if (state == PS_IN_LINE) {
			if (x == iw) {
				pg_btm = ln_btm = y;
				line = pi_line_new(page, ln_lft,
						   ln_top, ln_btm);
				pi_page_append_line(page, line);
				pg_rt = max(pg_rt, line->bbox.right);
				pg_lft = min(pg_lft, ln_lft);
				state = PS_BETWEEN_LINE;
			} else
				ln_lft = min(ln_lft, x);
		} else if (state == PS_BETWEEN_LINE) {
			if (x != iw) {
				ln_top = y;
				ln_lft = x;
				state = PS_IN_LINE;
			}
		} else {
			if (x != iw) {
				ln_top = pg_top = y;
				pg_lft = ln_lft = x;
				state = PS_IN_LINE;
			}
		}
	}

	if (state == PS_IN_LINE) {
		pg_btm = ln_btm = y;
		line = pi_line_new(page, ln_lft, ln_top, ln_btm);
		pi_page_append_line(page, line);
		pg_rt = max(pg_rt, line->bbox.right);
		pg_lft = min(pg_lft, ln_lft);
	}

	page->bbox.left = pg_lft;
	page->bbox.top = pg_top;
	page->bbox.right = pg_rt;
	page->bbox.bottom = pg_btm;
}

static struct pi_page *pi_page_new(const char *pgm_file)
{
	struct pi_page *page;

	page = malloc(sizeof(struct pi_page));
	error_exit_on(!page, -1, "Error alloc memory for pi_page.");
	memset(page, 0, sizeof(*page));
	INIT_LIST_HEAD(&page->lines);
	page->img = pi_image_load(pgm_file);
	pi_page_parse(page);

	return page;
}

void pi_page_free(struct pi_page *page)
{
	struct pi_line *l, *n;

	pi_lines_free(&page->lines);
	pi_image_free(page->img);
	free(page);
}

void pi_page_write(struct pi_page *page, FILE *fout)
{
	struct pi_line *line;
	struct pi_char *ch;
	struct pi_rect *bbox;

	bbox = &page->bbox;
	fprintf(fout, "page %d %d %d %d\n", bbox->left, bbox->top,
		bbox->right, bbox->bottom);

	pi_page_for_each_line(line, page) {
		bbox = &line->bbox;
		fprintf(fout, "line %d %d %d %d\n", bbox->left, bbox->top,
			bbox->right, bbox->bottom);
		pi_line_for_each_char(ch, line) {
			fprintf(fout, "char %d %d\n", ch->left, ch->right);
		}
	}
}

void pi_init(int *argc, char *argv[])
{
	pgm_init(argc, argv);
}

void usage(char *cmd)
{
	char *bcmd = basename(cmd);

	printf("usage: %s <pgm_file>\n", bcmd);
}

int main(int argc, char *argv[])
{
	int opt;
	struct pi_page *page;
	const char *pgm_file= NULL;

	while ((opt = getopt(argc, argv, "h")) != -1) {
		switch (opt) {
		case 'h':
			usage(argv[0]);
			return 0;
		default:
			usage(argv[0]);
			exit(-1);
		}
	}

	if (optind >= argc) {
		usage(argv[0]);
		exit(-1);
	}
	pgm_file = argv[optind];

	pi_init(&argc, argv);

	page = pi_page_new(pgm_file);
	pi_page_write(page, stdout);
	pi_page_free(page);

	return 0;
}
