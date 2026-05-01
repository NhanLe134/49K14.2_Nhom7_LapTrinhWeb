document.addEventListener('DOMContentLoaded', () => {
    const userBtn = document.getElementById('userDropdownBtn');
    const userMenu = document.getElementById('userMenu');

    if (userBtn && userMenu) {
        userBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenu.classList.toggle('show');
        });
    }

    // Custom Dropdown logic
    const dropdowns = document.querySelectorAll('.custom-dropdown');
    dropdowns.forEach(dropdown => {
        const header = dropdown.querySelector('.dropdown-header');
        const selected = dropdown.querySelector('.dropdown-selected');
        const list = dropdown.querySelector('.dropdown-list');
        const options = dropdown.querySelectorAll('.dropdown-option');
        const hiddenInput = dropdown.querySelector('input[type="hidden"]');

        header.addEventListener('click', (e) => {
            e.stopPropagation();
            // Close others
            dropdowns.forEach(d => {
                if (d !== dropdown) d.classList.remove('active');
            });
            dropdown.classList.toggle('active');
        });

        options.forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                selected.textContent = option.textContent;
                selected.style.color = '#333';
                if (hiddenInput) hiddenInput.value = option.textContent;
                dropdown.classList.remove('active');
            });
        });
    });

    // Datepicker logic
    const datepicker = document.getElementById('datepicker-depart');
    if (datepicker) {
        const header = datepicker.querySelector('.dropdown-header');
        const selectedDateStr = datepicker.querySelector('.date-selected');
        const hiddenInputDate = datepicker.querySelector('input[type="hidden"]');
        const grid = datepicker.querySelector('.calendar-grid');

        header.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdowns.forEach(d => d.classList.remove('active'));
            datepicker.classList.toggle('active');
        });

        let currentDate = new Date();

        function renderCalendar(date) {
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            const year = date.getFullYear();
            const month = date.getMonth();
            datepicker.querySelector('.month-year').textContent = new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(date);

            const firstDay = new Date(year, month, 1).getDay();
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const daysInPrevMonth = new Date(year, month, 0).getDate();

            let html = '<div class="weekday">Sun</div><div class="weekday">Mon</div><div class="weekday">Tue</div><div class="weekday">Wed</div><div class="weekday">Thu</div><div class="weekday">Fri</div><div class="weekday">Sat</div>';

            for (let i = firstDay - 1; i >= 0; i--) {
                html += `<div class="calendar-date other-month">${daysInPrevMonth - i}</div>`;
            }

            for (let i = 1; i <= daysInMonth; i++) {
                const cellDate = new Date(year, month, i);
                const isPast = cellDate < today;
                const dText = i === 1 ? '01' : i;
                const statusClass = isPast ? 'past-date' : 'current-month';

                html += `<div class="calendar-date ${statusClass}" data-date="${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}" ${isPast ? 'style="opacity: 0.3; cursor: not-allowed;"' : ''}>${dText}</div>`;
            }

            const totalCells = firstDay + daysInMonth;
            const nextDays = Math.ceil(totalCells / 7) * 7 - totalCells;
            for (let i = 1; i <= nextDays; i++) {
                html += `<div class="calendar-date other-month">${i}</div>`;
            }

            grid.innerHTML = html;

            grid.querySelectorAll('.current-month').forEach(cell => {
                cell.addEventListener('click', (e) => {
                    e.stopPropagation();
                    grid.querySelectorAll('.calendar-date').forEach(c => c.classList.remove('selected'));
                    cell.classList.add('selected');
                    const val = cell.getAttribute('data-date');
                    const parts = val.split('-');
                    selectedDateStr.textContent = `${parts[2]}/${parts[1]}/${parts[0]}`;
                    selectedDateStr.style.color = '#333';
                    if (hiddenInputDate) hiddenInputDate.value = val;
                    datepicker.classList.remove('active');
                });
            });
        }

        renderCalendar(currentDate);

        datepicker.querySelector('.fa-chevron-left').addEventListener('click', (e) => {
            e.stopPropagation();
            currentDate.setMonth(currentDate.getMonth() - 1);
            renderCalendar(currentDate);
        });

        datepicker.querySelector('.fa-chevron-right').addEventListener('click', (e) => {
            e.stopPropagation();
            currentDate.setMonth(currentDate.getMonth() + 1);
            renderCalendar(currentDate);
        });
    }

    document.addEventListener('click', () => {
        if (userMenu) userMenu.classList.remove('show');
        dropdowns.forEach(d => d.classList.remove('active'));
        if (datepicker) datepicker.classList.remove('active');
    });

    // Selecting seats logic
    const seatView = document.getElementById('seat-view');
    const seatCountEl = document.getElementById('seatCount');
    const totalPriceEl = document.getElementById('totalPrice');

    if (seatView) {
        seatView.addEventListener('click', (e) => {
            const seatItem = e.target.closest('.seat-item.available');
            if (seatItem) {
                seatItem.classList.toggle('selected');
                const selectedSeats = seatView.querySelectorAll('.seat-item.selected').length;
                if (seatCountEl) seatCountEl.textContent = selectedSeats;

                let basePrice = window.currentBookingTrip ? parseInt(String(window.currentBookingTrip.price || '150000').replace(/\D/g, '')) || 150000 : 150000;
                let priceNum = selectedSeats * basePrice;
                const priceStr = priceNum === 0 ? "0" : priceNum.toLocaleString('vi-VN').replace(',', '.');
                if (totalPriceEl) totalPriceEl.textContent = priceStr + ' vnđ';
            }
        });
    }

    // Real Search Results
    const btnSearch = document.querySelector('.btn-search');
    const resultsView = document.getElementById('results-view');
    const ticketsGrid = document.querySelector('.tickets-grid');

    window.currentBookingTrip = null;

    if (ticketsGrid) {
        ticketsGrid.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-choose-seat');
            if (btn) {
                const tripId = btn.getAttribute('data-trip-id');
                const card = btn.closest('.ticket-card');
                const priceStr = card.querySelector('.price').textContent;
                window.currentBookingTrip = { id: tripId, price: priceStr };

                fetch(`/api/lay_so_do_ghe?chuyen_id=${tripId}`)
                    .then(response => response.json())
                    .then(res => {
                        if (res.status === 'success') {
                            const seatMapCard = document.querySelector('.seat-map-card');
                            if (seatMapCard) {
                                const seatsData = res.data;
                                const seatCount = seatsData.length;

                                let layout = [];
                                if (seatCount <= 4) {
                                    layout = [['A2', 'A3', 'A4'], ['A1', null, 'STEERING']];
                                } else if (seatCount <= 7) {
                                    layout = [['B7', 'B6', 'B5'], ['B2', 'B3', 'B4'], ['B1', null, 'STEERING']];
                                } else {
                                    layout = [['C9', 'C8', 'C7'], ['C6', 'C5', 'C4'], ['C3', 'C2', 'C1'], [null, null, 'STEERING']];
                                }

                                let seatHtml = '';
                                layout.forEach(row => {
                                    seatHtml += '<div class="seat-row">';
                                    row.forEach(cell => {
                                        if (cell === 'STEERING') {
                                            seatHtml += `
                                                <div class="steering-wheel">
                                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" class="steering-svg" style="width: 45px; height: 45px; fill: #333;">
                                                        <circle cx="50" cy="50" r="36" stroke="currentColor" stroke-width="12" fill="none" />
                                                        <path d="M 14 46 Q 32 40 50 45 Q 68 40 86 46 L 86 54 L 60 54 L 56 86 L 44 86 L 40 54 L 14 54 Z" stroke="#333" stroke-width="2" stroke-linejoin="round" />
                                                        <circle cx="50" cy="50" r="16" fill="#333"/>
                                                        <circle cx="50" cy="50" r="6" fill="white" />
                                                    </svg>
                                                </div>`;
                                        } else if (cell === null) {
                                            seatHtml += '<div style="width: 50px;"></div>';
                                        } else {
                                            const seatInfo = seatsData.find(s => s.soGhe.toUpperCase() === cell.toUpperCase());
                                            const statusClass = seatInfo ? seatInfo.trangThai : 'available';
                                            seatHtml += `
                                                <div class="seat-item ${statusClass}" data-seat="${cell}">
                                                    <svg width="70" height="70" viewBox="0 0 70 70" fill="none" xmlns="http://www.w3.org/2000/svg" class="seat-svg">
                                                        <path d="M8.75 19.6875C8.75 16.7867 9.90234 14.0047 11.9535 11.9535C14.0047 9.90234 16.7867 8.75 19.6875 8.75H50.3125C53.2133 8.75 55.9953 9.90234 58.0465 11.9535C60.0977 14.0047 61.25 16.7867 61.25 19.6875V32.8125C60.0387 31.9036 58.6518 31.2561 57.1772 30.9112C55.7026 30.5662 54.1724 30.5312 52.6836 30.8084C51.1948 31.0856 49.7797 31.6689 48.5281 32.5215C47.2765 33.3741 46.2155 34.4773 45.4125 35.7612C44.1871 34.1639 42.6106 32.8698 40.8051 31.9792C38.9995 31.0885 37.0133 30.6252 35 30.625C30.7562 30.625 26.985 32.6375 24.5875 35.7612C23.7845 34.4773 22.7235 33.3741 21.4719 32.5215C20.2203 31.6689 18.8052 31.0856 17.3164 30.8084C15.8276 30.5312 14.2974 30.5662 12.8228 30.9112C11.3482 31.2561 9.96133 31.9036 8.75 32.8125V19.6875ZM43.75 43.75C43.75 41.4294 42.8281 39.2038 41.1872 37.5628C39.5462 35.9219 37.3206 35 35 35C32.6794 35 30.4538 35.9219 28.8128 37.5628C27.1719 39.2038 26.25 41.4294 26.25 43.75V61.25H43.75V43.75ZM48.125 61.25H53.5938C55.6243 61.25 57.5717 60.4434 59.0075 59.0075C60.4434 57.5717 61.25 55.6243 61.25 53.5938V41.5625C61.25 39.822 60.5586 38.1528 59.3279 36.9221C58.0972 35.6914 56.428 35 54.6875 35C52.947 35 51.2778 35.6914 50.0471 36.9221C48.8164 38.1528 48.125 39.822 48.125 41.5625V61.25ZM21.875 61.25H16.4062C14.3757 61.25 12.4283 60.4434 10.9925 59.0075C9.55664 57.5717 8.75 55.6243 8.75 53.5938V41.5625C8.75 40.7007 8.91974 39.8473 9.24954 39.0511C9.57934 38.2549 10.0627 37.5315 10.6721 36.9221C11.2815 36.3127 12.0049 35.8293 12.8011 35.4995C13.5973 35.1697 14.4507 35 15.3125 35C16.1743 35 17.0277 35.1697 17.8239 35.4995C18.6201 35.8293 19.3435 36.3127 19.9529 36.9221C20.5623 37.5315 21.0457 38.2549 21.3755 39.0511C21.7053 39.8473 21.875 40.7007 21.875 41.5625V61.25Z" fill="currentColor" />
                                                    </svg>
                                                    <span>${cell}</span>
                                                </div>`;
                                        }
                                    });
                                    seatHtml += '</div>';
                                });
                                seatMapCard.innerHTML = seatHtml;
                            }
                        } else {
                            alert('Không thể tải sơ đồ ghế: ' + res.message);
                        }
                    })
                    .catch(err => console.error('Lỗi fetch ghế:', err));

                if (seatCountEl) seatCountEl.textContent = '0';
                if (totalPriceEl) totalPriceEl.textContent = '0 vnđ';

                const timeStr = card.querySelector('.time').textContent;
                document.querySelectorAll('.dynamic-time').forEach(el => el.textContent = timeStr);

                if (resultsView) resultsView.style.display = 'none';
                if (seatView) seatView.style.display = 'block';
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    }

    // Info view trigger
    const btnSeatContinue = document.getElementById('btnSeatContinue');
    const infoView = document.getElementById('info-view');
    if (btnSeatContinue && infoView && seatView) {
        btnSeatContinue.addEventListener('click', (e) => {
            e.preventDefault();
            const selectedSeats = seatView.querySelectorAll('.seat-item.selected');
            if (selectedSeats.length > 0) {
                document.getElementById('postChuyenID').value = window.currentBookingTrip.id;
                const container = document.getElementById('selectedSeatsInputs');
                container.innerHTML = '';
                selectedSeats.forEach(s => {
                    const seatId = s.getAttribute('data-seat');
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'ghe_ids';
                    input.value = seatId;
                    container.appendChild(input);
                });

                seatView.style.display = 'none';
                infoView.style.display = 'block';
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
                alert('Vui lòng chọn ít nhất 1 chỗ!');
            }
        });
    }

    // Form validation
    const btnInfoContinue = document.getElementById('btnInfoContinue');
    if (btnInfoContinue) {
        const pickupInput = document.getElementById('pickupInput');
        const pickupError = document.getElementById('pickupError');
        const dropoffInput = document.getElementById('dropoffInput');
        const dropoffError = document.getElementById('dropoffError');
        const nameInput = document.getElementById('nameInput');
        const nameError = document.getElementById('nameError');
        const phoneInput = document.getElementById('phoneInput');
        const phoneError = document.getElementById('phoneError');

        const inputs = [pickupInput, dropoffInput, nameInput, phoneInput];
        const errors = [pickupError, dropoffError, nameError, phoneError];

        inputs.forEach((input, index) => {
            if (input) {
                input.addEventListener('input', () => {
                    input.classList.remove('error');
                    if (errors[index]) errors[index].style.display = 'none';
                });
            }
        });

        // Use global variables defined in HTML
        const originVal = window.bookingData ? window.bookingData.origin.toLowerCase() : "";
        const destVal = window.bookingData ? window.bookingData.destination.toLowerCase() : "";

        // Blur validations
        if (pickupInput) pickupInput.addEventListener('blur', () => {
            const val = pickupInput.value.trim().toLowerCase();
            if (!val) {
                pickupInput.classList.add('error');
                if (pickupError) { pickupError.textContent = 'Vui lòng nhập điểm đón'; pickupError.style.display = 'block'; }
            } else if (!val.includes(originVal)) {
                pickupInput.classList.add('error');
                if (pickupError) { pickupError.textContent = `Điểm đón không hợp lệ, thuộc ${originVal}`; pickupError.style.display = 'block'; }
            }
        });

        if (dropoffInput) dropoffInput.addEventListener('blur', () => {
            const val = dropoffInput.value.trim().toLowerCase();
            if (!val) {
                dropoffInput.classList.add('error');
                if (dropoffError) { dropoffError.textContent = 'Vui lòng nhập điểm trả'; dropoffError.style.display = 'block'; }
            } else if (!val.includes(destVal)) {
                dropoffInput.classList.add('error');
                if (dropoffError) { dropoffError.textContent = `Điểm trả không hợp lệ, thuộc ${destVal}`; dropoffError.style.display = 'block'; }
            }
        });

        const btnInfoBack = document.getElementById('btnInfoBack');
        if (btnInfoBack && seatView && infoView) {
            btnInfoBack.addEventListener('click', () => {
                infoView.style.display = 'none';
                seatView.style.display = 'block';
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }

        btnInfoContinue.addEventListener('click', (e) => {
            e.preventDefault();
            let hasError = false;

            // Re-validate strictly
            if (!pickupInput.value.trim().toLowerCase().includes(originVal)) {
                pickupInput.classList.add('error');
                pickupError.style.display = 'block';
                hasError = true;
            }
            if (!dropoffInput.value.trim().toLowerCase().includes(destVal)) {
                dropoffInput.classList.add('error');
                dropoffError.style.display = 'block';
                hasError = true;
            }
            if (!nameInput.value.trim()) {
                nameInput.classList.add('error');
                nameError.style.display = 'block';
                hasError = true;
            }
            if (!/^\d{10}$/.test(phoneInput.value.trim())) {
                phoneInput.classList.add('error');
                phoneError.style.display = 'block';
                hasError = true;
            }

            if (!hasError) {
                document.getElementById('finalBookingForm').submit();
            }
        });
    }

    // Success Modal Close
    const btnSuccessClose = document.getElementById('btnSuccessClose');
    if (btnSuccessClose) {
        btnSuccessClose.addEventListener('click', () => {
            const successModal = document.getElementById('success-modal');
            const infoV = document.getElementById('info-view');
            const seatV = document.getElementById('seat-view');
            const resultsV = document.getElementById('results-view');
            const searchV = document.getElementById('search-view');

            if (successModal) successModal.style.display = 'none';
            if (infoV) infoV.style.display = 'none';
            if (seatV) seatV.style.display = 'none';
            if (resultsV) resultsV.style.display = 'none';
            if (searchV) searchV.style.display = 'block';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});
