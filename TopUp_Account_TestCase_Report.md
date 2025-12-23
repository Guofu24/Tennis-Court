# BÁO CÁO PHÂN TÍCH VÀ THIẾT KẾ TEST CASE
## Chức năng: Top-up Account (Nạp tiền vào tài khoản)
## Phương pháp: Decision Table Testing

---

## MỤC LỤC
1. [Tổng quan chức năng](#1-tổng-quan-chức-năng)
2. [Phân tích yêu cầu từ code](#2-phân-tích-yêu-cầu-từ-code)
3. [Xác định Conditions và Actions](#3-xác-định-conditions-và-actions)
4. [Lập bảng Decision Table](#4-lập-bảng-decision-table)
5. [Giải thích các Rules](#5-giải-thích-các-rules)
6. [Bảng Test Cases](#6-bảng-test-cases)
7. [Ma trận Traceability](#7-ma-trận-traceability)

---

## 1. TỔNG QUAN CHỨC NĂNG

### 1.1 Mô tả chức năng
Chức năng Top-up Account cho phép người dùng đã xác thực nạp tiền vào tài khoản thông qua hai phương thức thanh toán:
- **Chuyển khoản ngân hàng (Bank Transfer)**: Hỗ trợ 8 ngân hàng Việt Nam
- **Ví điện tử (E-Wallet)**: Hỗ trợ 4 ví điện tử phổ biến

### 1.2 Các ngân hàng hỗ trợ
| ID | Tên ngân hàng |
|----|---------------|
| vcb | Vietcombank |
| tcb | Techcombank |
| mb | MB Bank |
| acb | ACB |
| bidv | BIDV |
| vib | VIB |
| vpb | VPBank |
| scb | Sacombank |

### 1.3 Các ví điện tử hỗ trợ
| ID | Tên ví điện tử |
|----|----------------|
| momo | Momo |
| zalopay | ZaloPay |
| vnpay | VNPay |
| shopeepay | ShopeePay |

### 1.4 Quick Amounts (Số tiền nhanh)
`[50, 100, 200, 500, 1000, 2000]` USD

---

## 2. PHÂN TÍCH YÊU CẦU TỪ CODE

### 2.1 Validation Rules (Trích xuất từ `views.py` - function `top_up`)

#### 2.1.1 Payment Type Validation
```python
if not payment_type:
    errors.append("Vui lòng chọn phương thức thanh toán.")
```
- **Điều kiện**: `payment_type` phải được chọn ('bank' hoặc 'wallet')

#### 2.1.2 Bank Transfer Validation
```python
# Card number validation (13-19 digits + Luhn algorithm)
if not card_number.isdigit():
    errors.append("Số thẻ chỉ được chứa chữ số.")
elif len(card_number) < 13 or len(card_number) > 19:
    errors.append("Số thẻ phải có từ 13-19 chữ số.")
else:
    # Luhn algorithm validation
    def luhn_check(card_num):
        def digits_of(n):
            return [int(d) for d in str(n)]
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0
```

```python
# Card expiry validation (MM/YY format)
if not re.match(r'^\d{2}/\d{2}$', card_expiry):
    errors.append("Ngày hết hạn phải theo định dạng MM/YY.")
else:
    month, year = card_expiry.split('/')
    month = int(month)
    year = int('20' + year)
    if month < 1 or month > 12:
        errors.append("Tháng hết hạn không hợp lệ (1-12).")
    else:
        if year < current_date.year or (year == current_date.year and month < current_date.month):
            errors.append("Thẻ đã hết hạn.")
```

```python
# CVV validation (3-4 digits)
if not card_cvv.isdigit() or len(card_cvv) < 3 or len(card_cvv) > 4:
    errors.append("Mã CVV phải có 3-4 chữ số.")
```

#### 2.1.3 E-Wallet Validation
```python
# Phone number validation (Vietnamese format)
phone_clean = re.sub(r'[\s\-\(\)]', '', phone_number)
if not re.match(r'^(0|\+84)(3|5|7|8|9)\d{8}$', phone_clean):
    errors.append("Số điện thoại không hợp lệ.")
```

```python
# OTP validation (6 digits)
if not otp_code.isdigit() or len(otp_code) != 6:
    errors.append("Mã OTP phải có đúng 6 chữ số.")
```

#### 2.1.4 Account Name Validation
```python
if len(account_name) < 2:
    errors.append("Tên chủ tài khoản phải có ít nhất 2 ký tự.")
elif len(account_name) > 100:
    errors.append("Tên chủ tài khoản không được quá 100 ký tự.")
else:
    if not re.match(r'^[\u00C0-\u024F\u1E00-\u1EFFa-zA-Z\s]+$', account_name):
        errors.append("Tên chủ tài khoản chỉ được chứa chữ cái và khoảng trắng.")
```

#### 2.1.5 Amount Validation
```python
top_up_amount = float(amount_str)
if top_up_amount <= 0:
    errors.append("Số tiền nạp phải lớn hơn 0.")
elif top_up_amount < 10:
    errors.append("Số tiền nạp tối thiểu là $10.")
elif top_up_amount > 10000:
    errors.append("Số tiền nạp tối đa là $10,000 mỗi lần.")
elif not (top_up_amount * 100).is_integer():
    errors.append("Số tiền chỉ được có tối đa 2 chữ số thập phân.")
```

#### 2.1.6 Daily Limit Validation
```python
today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
today_deposits = TransactionHistory.objects.filter(
    user=request.user,
    transaction_type='Deposit',
    timestamp__gte=today_start
).aggregate(total=Sum('amount'))['total'] or 0

if today_deposits + top_up_amount > 50000:
    errors.append(f"Đã vượt quá hạn mức nạp tiền trong ngày ($50,000).")
```

#### 2.1.7 Password Validation
```python
if not password:
    errors.append("Vui lòng nhập mật khẩu xác nhận.")
elif len(password) < 6:
    errors.append("Mật khẩu phải có ít nhất 6 ký tự.")
```

---

## 3. XÁC ĐỊNH CONDITIONS VÀ ACTIONS

### 3.1 CONDITIONS (Điều kiện)

#### 3.1.1 Decision Table 1: Bank Transfer Payment

| ID | Condition | Mô tả | Giá trị |
|----|-----------|-------|---------|
| C1 | Payment Type | Loại thanh toán | Bank |
| C2 | Bank Selected | Ngân hàng được chọn | Y/N |
| C3 | Card Number Format | Số thẻ chỉ chứa số | Y/N |
| C4 | Card Number Length | Độ dài số thẻ (13-19) | Y/N |
| C5 | Luhn Algorithm Valid | Thuật toán Luhn hợp lệ | Y/N |
| C6 | Expiry Format Valid | Định dạng MM/YY đúng | Y/N |
| C7 | Month Valid | Tháng hợp lệ (1-12) | Y/N |
| C8 | Card Not Expired | Thẻ chưa hết hạn | Y/N |
| C9 | CVV Valid | CVV 3-4 chữ số | Y/N |
| C10 | Account Name Valid | Tên hợp lệ (2-100 ký tự, chỉ chữ) | Y/N |
| C11 | Password Valid | Mật khẩu ≥ 6 ký tự | Y/N |
| C12 | Amount Valid | Số tiền $10-$10,000, 2 decimal | Y/N |
| C13 | Daily Limit OK | Chưa vượt $50,000/ngày | Y/N |

#### 3.1.2 Decision Table 2: E-Wallet Payment

| ID | Condition | Mô tả | Giá trị |
|----|-----------|-------|---------|
| C1 | Payment Type | Loại thanh toán | Wallet |
| C2 | Wallet Selected | Ví điện tử được chọn | Y/N |
| C3 | Phone Format Valid | Định dạng SĐT Việt Nam | Y/N |
| C4 | OTP Valid | OTP 6 chữ số | Y/N |
| C5 | Account Name Valid | Tên hợp lệ | Y/N |
| C6 | Password Valid | Mật khẩu ≥ 6 ký tự | Y/N |
| C7 | Amount Valid | Số tiền $10-$10,000 | Y/N |
| C8 | Daily Limit OK | Chưa vượt $50,000/ngày | Y/N |

### 3.2 ACTIONS (Hành động)

| ID | Action | Mô tả |
|----|--------|-------|
| A1 | Reject with Error | Từ chối giao dịch, hiển thị thông báo lỗi |
| A2 | Update Balance | Cập nhật số dư tài khoản người dùng |
| A3 | Create Transaction Record | Tạo bản ghi TransactionHistory |
| A4 | Generate Transaction ID | Tạo mã giao dịch TU-XXXXXXXXXXXX |
| A5 | Log Activity | Ghi log hoạt động nạp tiền |
| A6 | Show Success Message | Hiển thị thông báo thành công |
| A7 | Redirect to Property List | Chuyển hướng về trang danh sách |

---

## 4. LẬP BẢNG DECISION TABLE

### 4.1 Decision Table cho Bank Transfer

| Conditions/Actions | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 | R10 | R11 | R12 | R13 | R14 |
|-------------------|----|----|----|----|----|----|----|----|----|----|-----|-----|-----|-----|
| **CONDITIONS** |
| C1: Payment Type = Bank | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| C2: Bank Selected | N | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| C3: Card Number Format | - | N | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| C4: Card Number Length | - | - | N | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| C5: Luhn Algorithm Valid | - | - | - | N | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| C6: Expiry Format Valid | - | - | - | - | N | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| C7: Month Valid (1-12) | - | - | - | - | - | N | Y | Y | Y | Y | Y | Y | Y | Y |
| C8: Card Not Expired | - | - | - | - | - | - | N | Y | Y | Y | Y | Y | Y | Y |
| C9: CVV Valid (3-4 digits) | - | - | - | - | - | - | - | N | Y | Y | Y | Y | Y | Y |
| C10: Account Name Valid | - | - | - | - | - | - | - | - | N | Y | Y | Y | Y | Y |
| C11: Password Valid | - | - | - | - | - | - | - | - | - | N | Y | Y | Y | Y |
| C12: Amount Valid | - | - | - | - | - | - | - | - | - | - | N | Y | Y | Y |
| C13: Daily Limit OK | - | - | - | - | - | - | - | - | - | - | - | N | Y | Y |
| **ACTIONS** |
| A1: Reject with Error | X | X | X | X | X | X | X | X | X | X | X | X | - | - |
| A2: Update Balance | - | - | - | - | - | - | - | - | - | - | - | - | X | X |
| A3: Create Transaction Record | - | - | - | - | - | - | - | - | - | - | - | - | X | X |
| A4: Generate Transaction ID | - | - | - | - | - | - | - | - | - | - | - | - | X | X |
| A5: Log Activity | - | - | - | - | - | - | - | - | - | - | - | - | X | X |
| A6: Show Success Message | - | - | - | - | - | - | - | - | - | - | - | - | X | X |
| A7: Redirect | - | - | - | - | - | - | - | - | - | - | - | - | X | X |

**Ghi chú**: 
- Y = Yes (Có/Đúng)
- N = No (Không/Sai)  
- "-" = Don't care (Không áp dụng)
- X = Action được thực hiện

### 4.2 Decision Table cho E-Wallet Payment

| Conditions/Actions | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 |
|-------------------|----|----|----|----|----|----|----|----|-----|
| **CONDITIONS** |
| C1: Payment Type = Wallet | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| C2: Wallet Selected | N | Y | Y | Y | Y | Y | Y | Y | Y |
| C3: Phone Format Valid | - | N | Y | Y | Y | Y | Y | Y | Y |
| C4: OTP Valid (6 digits) | - | - | N | Y | Y | Y | Y | Y | Y |
| C5: Account Name Valid | - | - | - | N | Y | Y | Y | Y | Y |
| C6: Password Valid | - | - | - | - | N | Y | Y | Y | Y |
| C7: Amount Valid | - | - | - | - | - | N | Y | Y | Y |
| C8: Daily Limit OK | - | - | - | - | - | - | N | Y | Y |
| **ACTIONS** |
| A1: Reject with Error | X | X | X | X | X | X | X | - | - |
| A2: Update Balance | - | - | - | - | - | - | - | X | X |
| A3: Create Transaction Record | - | - | - | - | - | - | - | X | X |
| A4: Generate Transaction ID | - | - | - | - | - | - | - | X | X |
| A5: Log Activity | - | - | - | - | - | - | - | X | X |
| A6: Show Success Message | - | - | - | - | - | - | - | X | X |
| A7: Redirect | - | - | - | - | - | - | - | X | X |

### 4.3 Decision Table cho Amount Validation (Chi tiết)

| Conditions/Actions | R1 | R2 | R3 | R4 | R5 | R6 | R7 |
|-------------------|----|----|----|----|----|----|-----|
| **CONDITIONS** |
| C1: Amount is numeric | N | Y | Y | Y | Y | Y | Y |
| C2: Amount > 0 | - | N | Y | Y | Y | Y | Y |
| C3: Amount ≥ $10 | - | - | N | Y | Y | Y | Y |
| C4: Amount ≤ $10,000 | - | - | - | N | Y | Y | Y |
| C5: Max 2 decimal places | - | - | - | - | N | Y | Y |
| **ACTIONS** |
| A1: Error - Invalid number | X | - | - | - | - | - | - |
| A2: Error - Must be > 0 | - | X | - | - | - | - | - |
| A3: Error - Min $10 | - | - | X | - | - | - | - |
| A4: Error - Max $10,000 | - | - | - | X | - | - | - |
| A5: Error - 2 decimals max | - | - | - | - | X | - | - |
| A6: Amount Valid | - | - | - | - | - | X | X |

---

## 5. GIẢI THÍCH CÁC RULES

### 5.1 Bank Transfer Rules

| Rule | Điều kiện vi phạm | Error Message | Giải thích |
|------|-------------------|---------------|------------|
| R1 | Bank chưa được chọn | "Vui lòng chọn ngân hàng." | Người dùng chọn payment_type='bank' nhưng không chọn ngân hàng cụ thể |
| R2 | Card number không phải số | "Số thẻ chỉ được chứa chữ số." | Số thẻ chứa ký tự không phải số (chữ cái, ký tự đặc biệt) |
| R3 | Card number sai độ dài | "Số thẻ phải có từ 13-19 chữ số." | Số thẻ có ít hơn 13 hoặc nhiều hơn 19 chữ số |
| R4 | Luhn algorithm failed | "Số thẻ không hợp lệ (không đúng định dạng Luhn)." | Số thẻ không vượt qua kiểm tra thuật toán Luhn - không phải số thẻ thật |
| R5 | Expiry format sai | "Ngày hết hạn phải theo định dạng MM/YY." | Người dùng nhập sai format (ví dụ: 1/25, 01-25, 2025/01) |
| R6 | Month không hợp lệ | "Tháng hết hạn không hợp lệ (1-12)." | Tháng < 1 hoặc > 12 (ví dụ: 00/25, 13/25) |
| R7 | Thẻ đã hết hạn | "Thẻ đã hết hạn." | Năm < năm hiện tại, hoặc cùng năm nhưng tháng < tháng hiện tại |
| R8 | CVV không hợp lệ | "Mã CVV phải có 3-4 chữ số." | CVV không phải số hoặc không có 3-4 chữ số |
| R9 | Account name không hợp lệ | Multiple error messages | Tên < 2 ký tự, > 100 ký tự, hoặc chứa ký tự không phải chữ |
| R10 | Password không hợp lệ | "Mật khẩu phải có ít nhất 6 ký tự." | Mật khẩu trống hoặc < 6 ký tự |
| R11 | Amount không hợp lệ | Multiple error messages | Số tiền không nằm trong khoảng $10-$10,000 hoặc quá 2 chữ số thập phân |
| R12 | Vượt daily limit | "Đã vượt quá hạn mức nạp tiền trong ngày ($50,000)." | Tổng tiền nạp trong ngày (từ 00:00:00) + số tiền hiện tại > $50,000 |
| R13-R14 | Tất cả điều kiện đúng | Success | Giao dịch thành công, thực hiện tất cả actions |

### 5.2 E-Wallet Rules

| Rule | Điều kiện vi phạm | Error Message | Giải thích |
|------|-------------------|---------------|------------|
| R1 | Wallet chưa được chọn | "Vui lòng chọn ví điện tử." | Người dùng chọn payment_type='wallet' nhưng không chọn ví cụ thể |
| R2 | Phone format sai | "Số điện thoại không hợp lệ. Vui lòng nhập số điện thoại Việt Nam." | SĐT không khớp pattern `^(0|\+84)(3\|5\|7\|8\|9)\d{8}$` |
| R3 | OTP không hợp lệ | "Mã OTP phải có đúng 6 chữ số." | OTP không phải số hoặc không đúng 6 chữ số |
| R4 | Account name không hợp lệ | Multiple error messages | Tên không đáp ứng yêu cầu |
| R5 | Password không hợp lệ | "Mật khẩu phải có ít nhất 6 ký tự." | Mật khẩu không đáp ứng yêu cầu |
| R6 | Amount không hợp lệ | Multiple error messages | Số tiền không đáp ứng yêu cầu |
| R7 | Vượt daily limit | "Đã vượt quá hạn mức nạp tiền trong ngày ($50,000)." | Vượt giới hạn nạp tiền hàng ngày |
| R8-R9 | Tất cả điều kiện đúng | Success | Giao dịch thành công |

### 5.3 Luhn Algorithm Explanation

Thuật toán Luhn (còn gọi là "modulus 10" hoặc "mod 10") được sử dụng để validate số thẻ tín dụng:

```
Ví dụ với số thẻ: 4532015112830366

1. Bắt đầu từ chữ số cuối, nhân đôi mỗi chữ số ở vị trí chẵn
2. Nếu kết quả > 9, trừ đi 9
3. Cộng tất cả các chữ số lại
4. Nếu tổng chia hết cho 10, số thẻ hợp lệ
```

---

## 6. BẢNG TEST CASES

### 6.1 Test Cases cho Bank Transfer

| TC_ID | Test Case Name | Precondition | Input Data | Expected Result | Priority |
|-------|---------------|--------------|------------|-----------------|----------|
| **Card Number Validation** |
| TC_B001 | Empty card number | User logged in | card_number: "" | Error: "Vui lòng nhập số thẻ." | High |
| TC_B002 | Card with letters | User logged in | card_number: "4532a15112830366" | Error: "Số thẻ chỉ được chứa chữ số." | High |
| TC_B003 | Card with special chars | User logged in | card_number: "4532-0151-1283-0366" | Error: "Số thẻ chỉ được chứa chữ số." | Medium |
| TC_B004 | Card too short (12 digits) | User logged in | card_number: "453201511283" | Error: "Số thẻ phải có từ 13-19 chữ số." | High |
| TC_B005 | Card too long (20 digits) | User logged in | card_number: "45320151128303661234" | Error: "Số thẻ phải có từ 13-19 chữ số." | High |
| TC_B006 | Card min boundary (13 digits) | User logged in | card_number: "4532015112830" (valid Luhn) | Process next validation | High |
| TC_B007 | Card max boundary (19 digits) | User logged in | card_number: "4532015112830366123" (valid Luhn) | Process next validation | High |
| TC_B008 | Invalid Luhn checksum | User logged in | card_number: "4532015112830367" | Error: "Số thẻ không hợp lệ (không đúng định dạng Luhn)." | Critical |
| TC_B009 | Valid Luhn checksum | User logged in | card_number: "4532015112830366" | Passes Luhn validation | Critical |
| **Card Expiry Validation** |
| TC_B010 | Empty expiry date | User logged in | card_expiry: "" | Error: "Vui lòng nhập ngày hết hạn thẻ." | High |
| TC_B011 | Wrong format (slash missing) | User logged in | card_expiry: "1225" | Error: "Ngày hết hạn phải theo định dạng MM/YY." | High |
| TC_B012 | Wrong format (dash) | User logged in | card_expiry: "12-25" | Error: "Ngày hết hạn phải theo định dạng MM/YY." | Medium |
| TC_B013 | Wrong format (single digit month) | User logged in | card_expiry: "1/25" | Error: "Ngày hết hạn phải theo định dạng MM/YY." | High |
| TC_B014 | Invalid month (00) | User logged in | card_expiry: "00/25" | Error: "Tháng hết hạn không hợp lệ (1-12)." | High |
| TC_B015 | Invalid month (13) | User logged in | card_expiry: "13/25" | Error: "Tháng hết hạn không hợp lệ (1-12)." | High |
| TC_B016 | Valid month boundary (01) | User logged in | card_expiry: "01/26" | Passes month validation | Medium |
| TC_B017 | Valid month boundary (12) | User logged in | card_expiry: "12/26" | Passes month validation | Medium |
| TC_B018 | Expired card (past year) | User logged in | card_expiry: "12/24" (current: 12/2025) | Error: "Thẻ đã hết hạn." | Critical |
| TC_B019 | Expired card (same year, past month) | User logged in | card_expiry: "11/25" (current: 12/2025) | Error: "Thẻ đã hết hạn." | Critical |
| TC_B020 | Valid card (same month) | User logged in | card_expiry: "12/25" (current: 12/2025) | Passes expiry validation | High |
| TC_B021 | Valid card (future) | User logged in | card_expiry: "06/28" | Passes expiry validation | High |
| **CVV Validation** |
| TC_B022 | Empty CVV | User logged in | card_cvv: "" | Error: "Vui lòng nhập mã CVV." | High |
| TC_B023 | CVV with letters | User logged in | card_cvv: "12a" | Error: "Mã CVV phải có 3-4 chữ số." | High |
| TC_B024 | CVV too short (2 digits) | User logged in | card_cvv: "12" | Error: "Mã CVV phải có 3-4 chữ số." | High |
| TC_B025 | CVV too long (5 digits) | User logged in | card_cvv: "12345" | Error: "Mã CVV phải có 3-4 chữ số." | High |
| TC_B026 | Valid CVV (3 digits) | User logged in | card_cvv: "123" | Passes CVV validation | High |
| TC_B027 | Valid CVV (4 digits) | User logged in | card_cvv: "1234" | Passes CVV validation | High |

### 6.2 Test Cases cho E-Wallet

| TC_ID | Test Case Name | Precondition | Input Data | Expected Result | Priority |
|-------|---------------|--------------|------------|-----------------|----------|
| **Phone Number Validation** |
| TC_W001 | Empty phone number | User logged in | phone_number: "" | Error: "Vui lòng nhập số điện thoại." | High |
| TC_W002 | Invalid prefix (02) | User logged in | phone_number: "0212345678" | Error: "Số điện thoại không hợp lệ." | High |
| TC_W003 | Too short | User logged in | phone_number: "09123456" | Error: "Số điện thoại không hợp lệ." | High |
| TC_W004 | Too long | User logged in | phone_number: "091234567890" | Error: "Số điện thoại không hợp lệ." | High |
| TC_W005 | With letters | User logged in | phone_number: "0912345a78" | Error: "Số điện thoại không hợp lệ." | High |
| TC_W006 | Valid - prefix 03 | User logged in | phone_number: "0312345678" | Passes phone validation | High |
| TC_W007 | Valid - prefix 05 | User logged in | phone_number: "0512345678" | Passes phone validation | High |
| TC_W008 | Valid - prefix 07 | User logged in | phone_number: "0712345678" | Passes phone validation | High |
| TC_W009 | Valid - prefix 08 | User logged in | phone_number: "0812345678" | Passes phone validation | High |
| TC_W010 | Valid - prefix 09 | User logged in | phone_number: "0912345678" | Passes phone validation | High |
| TC_W011 | Valid - prefix +84 | User logged in | phone_number: "+84912345678" | Passes phone validation | High |
| TC_W012 | With spaces (removed) | User logged in | phone_number: "091 234 5678" | Passes phone validation | Medium |
| **OTP Validation** |
| TC_W013 | Empty OTP | User logged in | otp_code: "" | Error: "Vui lòng nhập mã OTP." | High |
| TC_W014 | OTP too short (5 digits) | User logged in | otp_code: "12345" | Error: "Mã OTP phải có đúng 6 chữ số." | High |
| TC_W015 | OTP too long (7 digits) | User logged in | otp_code: "1234567" | Error: "Mã OTP phải có đúng 6 chữ số." | High |
| TC_W016 | OTP with letters | User logged in | otp_code: "12345a" | Error: "Mã OTP phải có đúng 6 chữ số." | High |
| TC_W017 | Valid OTP | User logged in | otp_code: "123456" | Passes OTP validation | High |

### 6.3 Test Cases cho Account Name

| TC_ID | Test Case Name | Precondition | Input Data | Expected Result | Priority |
|-------|---------------|--------------|------------|-----------------|----------|
| TC_N001 | Empty account name | User logged in | account_name: "" | Error: "Vui lòng nhập tên chủ tài khoản." | High |
| TC_N002 | Too short (1 char) | User logged in | account_name: "A" | Error: "Tên chủ tài khoản phải có ít nhất 2 ký tự." | High |
| TC_N003 | Min boundary (2 chars) | User logged in | account_name: "AB" | Passes name validation | Medium |
| TC_N004 | Max boundary (100 chars) | User logged in | account_name: "A" * 100 | Passes name validation | Medium |
| TC_N005 | Too long (101 chars) | User logged in | account_name: "A" * 101 | Error: "Tên chủ tài khoản không được quá 100 ký tự." | High |
| TC_N006 | Contains numbers | User logged in | account_name: "Nguyen Van 123" | Error: "Tên chỉ được chứa chữ cái và khoảng trắng." | High |
| TC_N007 | Contains special chars | User logged in | account_name: "Nguyen@Van" | Error: "Tên chỉ được chứa chữ cái và khoảng trắng." | High |
| TC_N008 | Vietnamese characters | User logged in | account_name: "Nguyễn Văn Anh" | Passes name validation | Critical |
| TC_N009 | Only spaces | User logged in | account_name: "   " | Error (after strip) | Medium |

### 6.4 Test Cases cho Amount

| TC_ID | Test Case Name | Precondition | Input Data | Expected Result | Priority |
|-------|---------------|--------------|------------|-----------------|----------|
| TC_A001 | Empty amount | User logged in | amount: "" | Error: "Vui lòng nhập số tiền nạp." | High |
| TC_A002 | Non-numeric amount | User logged in | amount: "abc" | Error: "Số tiền không hợp lệ." | High |
| TC_A003 | Negative amount | User logged in | amount: "-50" | Error: "Số tiền nạp phải lớn hơn 0." | High |
| TC_A004 | Zero amount | User logged in | amount: "0" | Error: "Số tiền nạp phải lớn hơn 0." | High |
| TC_A005 | Below minimum ($9.99) | User logged in | amount: "9.99" | Error: "Số tiền nạp tối thiểu là $10." | Critical |
| TC_A006 | Min boundary ($10) | User logged in | amount: "10" | Passes amount validation | Critical |
| TC_A007 | Above maximum ($10,001) | User logged in | amount: "10001" | Error: "Số tiền nạp tối đa là $10,000." | Critical |
| TC_A008 | Max boundary ($10,000) | User logged in | amount: "10000" | Passes amount validation | Critical |
| TC_A009 | Valid 2 decimals | User logged in | amount: "50.55" | Passes amount validation | High |
| TC_A010 | Invalid 3 decimals | User logged in | amount: "50.555" | Error: "Số tiền chỉ được có tối đa 2 chữ số thập phân." | High |
| TC_A011 | Quick amount $50 | User logged in | amount: "50" | Passes amount validation | High |
| TC_A012 | Quick amount $2000 | User logged in | amount: "2000" | Passes amount validation | High |

### 6.5 Test Cases cho Daily Limit

| TC_ID | Test Case Name | Precondition | Input Data | Expected Result | Priority |
|-------|---------------|--------------|------------|-----------------|----------|
| TC_D001 | First deposit of day | today_deposits = 0 | amount: "1000" | Passes daily limit check | High |
| TC_D002 | Under daily limit | today_deposits = 40000 | amount: "9999" | Passes daily limit check | High |
| TC_D003 | At daily limit boundary | today_deposits = 40000 | amount: "10000" | Passes daily limit check | Critical |
| TC_D004 | Exceed daily limit by $1 | today_deposits = 40001 | amount: "10000" | Error: "Đã vượt quá hạn mức..." | Critical |
| TC_D005 | Already at limit | today_deposits = 50000 | amount: "10" | Error: "Đã vượt quá hạn mức..." | Critical |
| TC_D006 | Deposit after midnight reset | today_deposits reset to 0 | amount: "10000" | Passes daily limit check | High |

### 6.6 Test Cases cho Password Validation

| TC_ID | Test Case Name | Precondition | Input Data | Expected Result | Priority |
|-------|---------------|--------------|------------|-----------------|----------|
| TC_P001 | Empty password | User logged in | password: "" | Error: "Vui lòng nhập mật khẩu xác nhận." | High |
| TC_P002 | Too short (5 chars) | User logged in | password: "12345" | Error: "Mật khẩu phải có ít nhất 6 ký tự." | High |
| TC_P003 | Min boundary (6 chars) | User logged in | password: "123456" | Passes password validation | High |
| TC_P004 | Long password | User logged in | password: "verysecurepassword123" | Passes password validation | Medium |

### 6.7 Integration Test Cases (End-to-End)

| TC_ID | Test Case Name | Precondition | Input Data | Expected Result | Priority |
|-------|---------------|--------------|------------|-----------------|----------|
| TC_E001 | Successful Bank Transfer | User logged in, balance=100 | All valid bank inputs, amount=500 | Balance=600, Transaction created, Success message | Critical |
| TC_E002 | Successful E-Wallet | User logged in, balance=0 | All valid wallet inputs, amount=100 | Balance=100, Transaction created | Critical |
| TC_E003 | Transaction ID format | User logged in | Valid inputs | Transaction ID matches TU-XXXXXXXXXXXX format | High |
| TC_E004 | Multiple errors | User logged in | Multiple invalid inputs | All errors displayed | Medium |
| TC_E005 | Balance update real-time | User logged in | Valid inputs | Balance updates without page refresh | High |
| TC_E006 | Activity logged | User logged in | Valid inputs | UserActivity record created with correct data | High |

---

## 7. MA TRẬN TRACEABILITY

### 7.1 Requirements to Test Cases Mapping

| Requirement ID | Requirement Description | Test Cases |
|----------------|------------------------|------------|
| REQ-01 | Card number 13-19 digits | TC_B004, TC_B005, TC_B006, TC_B007 |
| REQ-02 | Luhn algorithm validation | TC_B008, TC_B009 |
| REQ-03 | Card expiry MM/YY format | TC_B010-TC_B013 |
| REQ-04 | Reject expired cards | TC_B018, TC_B019, TC_B020, TC_B021 |
| REQ-05 | CVV 3-4 digits | TC_B022-TC_B027 |
| REQ-06 | Vietnamese phone format | TC_W001-TC_W012 |
| REQ-07 | OTP 6 digits | TC_W013-TC_W017 |
| REQ-08 | Amount $10-$10,000 | TC_A005-TC_A008 |
| REQ-09 | Max 2 decimal places | TC_A009, TC_A010 |
| REQ-10 | Daily limit $50,000 | TC_D001-TC_D006 |
| REQ-11 | Transaction ID format | TC_E003 |
| REQ-12 | Balance update | TC_E001, TC_E002, TC_E005 |
| REQ-13 | Activity logging | TC_E006 |

### 7.2 Test Coverage Summary

| Category | Total Test Cases | Priority Distribution |
|----------|-----------------|----------------------|
| Card Number | 9 | Critical: 2, High: 6, Medium: 1 |
| Card Expiry | 12 | Critical: 2, High: 8, Medium: 2 |
| CVV | 6 | High: 6 |
| Phone Number | 12 | High: 11, Medium: 1 |
| OTP | 5 | High: 5 |
| Account Name | 9 | Critical: 1, High: 6, Medium: 2 |
| Amount | 12 | Critical: 4, High: 8 |
| Daily Limit | 6 | Critical: 2, High: 4 |
| Password | 4 | High: 3, Medium: 1 |
| Integration | 6 | Critical: 2, High: 4 |
| **TOTAL** | **81** | **Critical: 13, High: 57, Medium: 7** |

---

## 8. PHỤ LỤC

### 8.1 Test Data Examples

#### Valid Card Numbers (Pass Luhn)
- `4532015112830366` (Visa)
- `5425233430109903` (Mastercard)
- `374245455400126` (Amex - 15 digits)

#### Invalid Card Numbers (Fail Luhn)
- `4532015112830367`
- `1234567890123456`
- `0000000000000000`

#### Valid Vietnamese Phone Numbers
- `0912345678`
- `0312345678`
- `+84912345678`
- `+84312345678`

#### Invalid Vietnamese Phone Numbers
- `0212345678` (prefix 02 không hợp lệ)
- `0112345678` (prefix 01 không hợp lệ)
- `091234567` (thiếu 1 số)
- `09123456789` (thừa 1 số)

### 8.2 Transaction Record Structure

```python
TransactionHistory:
    user: CustomUser (FK)
    transaction_type: 'Deposit'
    payment_method: 'bank_transfer' | 'momo' | 'zalopay' | 'vnpay'
    amount: Float
    timestamp: DateTime (auto)
```

### 8.3 Activity Log Structure

```python
log_activity(request, 'top_up', f'Nạp tiền ${amount}', {
    'amount': amount,
    'payment_type': 'bank' | 'wallet',
    'bank': bank_id,
    'wallet': wallet_id,
    'transaction_id': 'TU-XXXXXXXXXXXX',
    'new_balance': new_balance
})
```

---

**Document Version**: 1.0  
**Created Date**: December 22, 2025  
**Author**: Test Analysis Team  
**Based on**: `home/views.py` - function `top_up()`  
**Code Analysis Reference**: Lines 549-752
