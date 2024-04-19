document.addEventListener('alpine:init', () => {
    Alpine.data('tableBackupSchedules', () => ({
        selected: [],
        clickRow(id) {
            if (this.selected.includes(id)) {
                this.selected = this.selected.filter((item) => item !== id)
            } else {
                this.selected.push(id)
            }
        },
        deleteSelected() {
            htmx.ajax(
                "DELETE",
                "/volumes/backup/schedules",
                {
                    source: "closest form",
                    target: "#backup-schedule-rows",
                    values: { "schedules": this.selected }
                }
            )
            this.selected = []
        }

    }))
    Alpine.data('tableBackupRestore', () => ({
        selected: [],
        clickRow(id) {
            if (this.selected.some(item => item["backup_id"] === id)){
                this.selected = this.selected.filter((item) => item["backup_id"] !== id)
            } else {
                this.selected.push({"backup_id": id, "volume_name": ""})
            }
        },
        isSelected(id) {
            return this.selected.some(item => item["backup_id"] === id)
        },
        restoreVolumes() {
            htmx.ajax(
                "POST",
                "/volumes/restore",
                {
                    source: "closest form",
                    target: "#notifications",
                    values: { "volumes": this.selected }
                }
            )
            this.selected = []
        }
    }))
    Alpine.data('draggableWindow', () => ({
        dragging: false,
        offsetX: 0,
        offsetY: 0,
        init() {
            let windowPosition = JSON.parse(localStorage.getItem(`${this.$root.id}windowPosition`));
            if (windowPosition) {
                this.$root.style.left = windowPosition.left;
                this.$root.style.top = windowPosition.top;
                this.$root.style.width = windowPosition.width;
                this.$root.style.height = windowPosition.height;
            }
        },
        startDrag() {
            if (!this.$root.style.width ||  this.$root.style.width !== '100%') {
                this.dragging = true
                this.offsetX = this.$event.clientX - this.$root.offsetLeft
                this.offsetY = this.$event.clientY - this.$root.offsetTop
            }
        },
        drag() {
            if (this.dragging) {
                this.$root.style.left = (this.$event.clientX - this.offsetX) + 'px'
                this.$root.style.top = (this.$event.clientY - this.offsetY) + 'px'
            }
        },
        stopDrag() {
            this.dragging = false
            let windowPosition = {
                left: this.$root.style.left,
                top: this.$root.style.top,
                width: this.$root.style.width,
                height: this.$root.style.height
            };
            localStorage.setItem(`${this.$root.id}windowPosition`, JSON.stringify(windowPosition));
        },
        expandWindow(){
            // TODO there could be a better way to handle not being able to expand the window in smaller window sizes
            const style = window.getComputedStyle(this.$root);
            const widthPx = parseInt(style.width);
            const isMiniumWidth = widthPx < 629;
            const isFullWidth = !this.$root.style.width || this.$root.style.width === '100%'
            const canExpand = !isMiniumWidth && isFullWidth;
            if (canExpand) {
                this.$root.style.width = '50%'
                let windowPosition = {
                    width: this.$root.style.width,
                    height: this.$root.style.height
                };
                localStorage.setItem(`${this.$root.id}windowPosition`, JSON.stringify(windowPosition));
            } else {
                this.$root.style.width = '100%';
                this.$root.style.left = '0';
                this.$root.style.top = '0';
                localStorage.removeItem(`${this.$root.id}windowPosition`);
            }
        }
    }))

    Alpine.store('windowState', {
        mainWindowState: Alpine.$persist({tabState: "backup-volumes"}),
        switchTab(tab) {
            this.mainWindowState.tabState = tab
        }
    });
})
