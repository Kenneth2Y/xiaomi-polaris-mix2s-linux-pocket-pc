/* SPDX-License-Identifier: MIT */
/* Count USB input events only; never grab devices, inject, or print key codes. */
#include <linux/input.h>

struct input_counter {
	int fd;
	unsigned long presses, releases, repeats, relative, frames, dropped;
};

int main(int argc, char **argv)
{
	struct input_counter devices[32];
	struct timespec start, now;
	int count = 0, seconds = 30;

	if (argc == 2 && !strcmp(argv[1], "--describe")) {
		puts("USB input monitor: read-only, no grabs/injection/key-code logging.");
		return 0;
	}
	if (argc == 2) {
		seconds = atoi(argv[1]);
		if (seconds < 1 || seconds > 60)
			return 2;
	}
	for (int i = 0; i < 32; i++) {
		char path[64], name[160] = { 0 };
		struct input_id id;
		int fd;

		snprintf(path, sizeof(path), "/dev/input/event%d", i);
		fd = open(path, O_RDONLY | O_NONBLOCK);
		if (fd < 0)
			continue;
		if (ioctl(fd, EVIOCGID, &id) || id.bustype != BUS_USB) {
			close(fd);
			continue;
		}
		if (ioctl(fd, EVIOCGNAME(sizeof(name)), name) < 0) {
			close(fd);
			continue;
		}
		memset(&devices[count], 0, sizeof(devices[count]));
		devices[count++].fd = fd;
		printf("MONITOR %s name=%s\n", path, name);
	}
	if (!count) {
		puts("No USB input devices found.");
		return 3;
	}
	if (clock_gettime(CLOCK_MONOTONIC, &start))
		return 1;
	printf("READY USB_devices=%d seconds=%d\n", count, seconds);
	for (;;) {
		if (clock_gettime(CLOCK_MONOTONIC, &now))
			return 1;
		if (now.tv_sec - start.tv_sec >= seconds)
			break;
		for (int i = 0; i < count; i++) {
			struct input_event events[64];
			ssize_t bytes = read(devices[i].fd, events, sizeof(events));

			if (bytes < 0) {
				if (errno != EAGAIN && errno != EINTR) {
					perror("read USB input");
					return 1;
				}
				continue;
			}
			if (!bytes || bytes % sizeof(events[0]))
				return 1;
			for (int j = 0; j < bytes / sizeof(events[0]); j++) {
				struct input_event *e = &events[j];
				if (e->type == EV_KEY) {
					if (e->value == 1) devices[i].presses++;
					if (e->value == 0) devices[i].releases++;
					if (e->value == 2) devices[i].repeats++;
				}
				if (e->type == EV_REL) devices[i].relative++;
				if (e->type == EV_SYN && e->code == SYN_REPORT) devices[i].frames++;
				if (e->type == EV_SYN && e->code == SYN_DROPPED) devices[i].dropped++;
			}
		}
		usleep(10000);
	}
	for (int i = 0; i < count; i++) {
		printf("SUMMARY fd=%d presses=%lu releases=%lu repeats=%lu relative=%lu frames=%lu dropped=%lu\n",
		       devices[i].fd, devices[i].presses, devices[i].releases,
		       devices[i].repeats, devices[i].relative, devices[i].frames, devices[i].dropped);
		close(devices[i].fd);
	}
	return 0;
}
