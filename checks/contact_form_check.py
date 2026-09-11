def check_contact_forms(page):
    """
    Check contact forms on the current webpage.

    Checks:
    1. Detect forms
    2. Identify likely contact forms
    3. Check visibility
    4. Detect input fields
    5. Detect name/email/phone/message fields
    6. Check required fields
    7. Check field labels / accessibility names
    8. Detect submit button
    9. Detect CAPTCHA / anti-spam
    10. Detect form method/action

    Important:
    This check does NOT submit the form.
    It avoids sending real messages during QA.
    """

    print("\nContact Form Check")
    print("------------------")

    # =====================================
    # COLLECT FORM INFORMATION
    # =====================================

    forms = page.evaluate("""
        () => {

            const forms =
                Array.from(
                    document.querySelectorAll(
                        "form"
                    )
                );

            return forms.map(
                (form, formIndex) => {

                    const formRect =
                        form.getBoundingClientRect();

                    const formStyle =
                        window.getComputedStyle(
                            form
                        );

                    const formVisible = (
                        formStyle.display !== "none" &&
                        formStyle.visibility !== "hidden" &&
                        Number(formStyle.opacity) !== 0 &&
                        formRect.width > 0 &&
                        formRect.height > 0
                    );


                    // =================================
                    // FORM FIELDS
                    // =================================

                    const elements =
                        Array.from(
                            form.querySelectorAll(
                                "input, textarea, select"
                            )
                        );

                    const fields = [];


                    for (
                        const element of
                        elements
                    ) {

                        const tag =
                            element.tagName
                            .toLowerCase();

                        const type =
                            (
                                element.getAttribute(
                                    "type"
                                ) ||
                                tag
                            )
                            .toLowerCase();


                        // Skip submit controls here.
                        // They are checked separately.
                        if (
                            type === "submit" ||
                            type === "button" ||
                            type === "reset"
                        ) {
                            continue;
                        }


                        const rect =
                            element
                            .getBoundingClientRect();

                        const style =
                            window
                            .getComputedStyle(
                                element
                            );


                        const visible = (
                            style.display !== "none" &&
                            style.visibility !== "hidden" &&
                            Number(style.opacity) !== 0 &&
                            rect.width > 0 &&
                            rect.height > 0
                        );


                        // =================================
                        // FIND LABEL
                        // =================================

                        let labelText = "";


                        // Explicit:
                        // <label for="email">
                        if (element.id) {

                            const label =
                                form.querySelector(
                                    `label[for="${CSS.escape(
                                        element.id
                                    )}"]`
                                );

                            if (label) {

                                labelText =
                                    (
                                        label.innerText ||
                                        ""
                                    ).trim();
                            }
                        }


                        // Wrapped:
                        // <label><input></label>
                        if (!labelText) {

                            const parentLabel =
                                element.closest(
                                    "label"
                                );

                            if (parentLabel) {

                                labelText =
                                    (
                                        parentLabel.innerText ||
                                        ""
                                    ).trim();
                            }
                        }


                        // Accessibility fallback
                        const ariaLabel =
                            (
                                element.getAttribute(
                                    "aria-label"
                                ) ||
                                ""
                            ).trim();


                        const placeholder =
                            (
                                element.getAttribute(
                                    "placeholder"
                                ) ||
                                ""
                            ).trim();


                        fields.push({
                            tag:
                                tag,

                            type:
                                type,

                            name:
                                element.getAttribute(
                                    "name"
                                ) || "",

                            id:
                                element.id || "",

                            placeholder:
                                placeholder,

                            label:
                                labelText,

                            ariaLabel:
                                ariaLabel,

                            required:
                                element.required ||
                                element.getAttribute(
                                    "aria-required"
                                ) === "true",

                            disabled:
                                element.disabled,

                            visible:
                                visible
                        });
                    }


                    // =================================
                    // SUBMIT BUTTONS
                    // =================================

                    const submitElements =
                        Array.from(
                            form.querySelectorAll(
                                [
                                    'button[type="submit"]',
                                    'input[type="submit"]',
                                    'button:not([type])'
                                ].join(",")
                            )
                        );


                    const submitButtons =
                        submitElements.map(
                            button => {

                                const rect =
                                    button
                                    .getBoundingClientRect();

                                const style =
                                    window
                                    .getComputedStyle(
                                        button
                                    );

                                return {
                                    text:
                                        (
                                            button.innerText ||
                                            button.value ||
                                            button.getAttribute(
                                                "aria-label"
                                            ) ||
                                            ""
                                        )
                                        .trim()
                                        .replace(
                                            /\\s+/g,
                                            " "
                                        )
                                        .slice(
                                            0,
                                            100
                                        ),

                                    disabled:
                                        button.disabled,

                                    visible:
                                        (
                                            style.display !== "none" &&
                                            style.visibility !== "hidden" &&
                                            Number(style.opacity) !== 0 &&
                                            rect.width > 0 &&
                                            rect.height > 0
                                        )
                                };
                            }
                        );


                    // =================================
                    // CAPTCHA / ANTI-SPAM
                    // =================================

                    const captchaSelectors = [
                        ".g-recaptcha",
                        "[data-sitekey]",
                        ".cf-turnstile",
                        "[class*='recaptcha']",
                        "[id*='recaptcha']",
                        "[class*='captcha']",
                        "[name*='honeypot']",
                        "[class*='honeypot']"
                    ];


                    let captchaDetected = false;


                    for (
                        const selector of
                        captchaSelectors
                    ) {

                        if (
                            form.querySelector(
                                selector
                            )
                        ) {

                            captchaDetected = true;
                            break;
                        }
                    }


                    // =================================
                    // FORM INFORMATION
                    // =================================

                    return {
                        index:
                            formIndex + 1,

                        id:
                            form.id || "",

                        className:
                            typeof form.className ===
                            "string"
                                ? form.className
                                : "",

                        action:
                            form.getAttribute(
                                "action"
                            ) || "",

                        method:
                            (
                                form.getAttribute(
                                    "method"
                                ) ||
                                "GET"
                            ).toUpperCase(),

                        visible:
                            formVisible,

                        fields:
                            fields,

                        submitButtons:
                            submitButtons,

                        captchaDetected:
                            captchaDetected
                    };
                }
            );
        }
    """)

    # =====================================
    # NO FORMS
    # =====================================

    if not forms:

        print(
            "WARNING | Form Detection |",
            "No forms detected on this page"
        )

        print(
            "\nContact Form Check Complete"
        )

        print(
            "---------------------------"
        )

        return

    print(
        "PASS | Form Detection |",
        len(forms),
        "form(s) detected"
    )

    # =====================================
    # IDENTIFY LIKELY CONTACT FORMS
    # =====================================

    contact_forms = []


    for form in forms:

        # -------------------------------------
        # NORMALIZE FORM INFORMATION
        # -------------------------------------

        form_id = (
            form["id"]
            or ""
        ).lower()

        form_class = (
            form["className"]
            or ""
        ).lower()

        form_action = (
            form["action"]
            or ""
        ).lower()


        # =====================================
        # IGNORE GOOGLE TRANSLATE /
        # SYSTEM FORMS
        # =====================================

        if (
            form_id.startswith(
                "goog-"
            )
            or
            "translate.googleapis.com"
            in form_action
            or
            "translate.google.com"
            in form_action
        ):

            continue


        # =====================================
        # DETECT KNOWN CONTACT FORM PLUGINS
        # =====================================

        known_contact_classes = [
            "elementor-form",
            "wpcf7",
            "wpforms",
            "fluentform",
            "forminator",
            "gform_wrapper",
            "gravity-form",
            "contact-form"
        ]


        class_match = any(
            keyword in form_class
            for keyword
            in known_contact_classes
        )


        # =====================================
        # BUILD FIELD SEARCH TEXT
        # =====================================

        field_text_parts = []


        for field in form[
            "fields"
        ]:

            field_text_parts.extend(
                [
                    field["name"],
                    field["id"],
                    field["placeholder"],
                    field["label"],
                    field["ariaLabel"],
                    field["type"]
                ]
            )


        field_text = (
            " ".join(
                field_text_parts
            )
            .lower()
        )


        # =====================================
        # DETECT CONTACT-LIKE FIELDS
        # =====================================

        has_email = (
            "email" in field_text
            or
            "e-mail" in field_text
        )

        has_name = (
            "name" in field_text
        )

        has_phone = (
            "phone" in field_text
            or
            "mobile" in field_text
            or
            "telephone" in field_text
            or
            "tel" in field_text
        )

        has_message = (
            "message" in field_text
            or
            "comment" in field_text
            or
            "enquiry" in field_text
            or
            "inquiry" in field_text
            or
            "textarea" in field_text
        )


        field_match = (
            has_email
            and
            (
                has_name
                or
                has_phone
                or
                has_message
            )
        )


        # =====================================
        # FINAL CONTACT FORM DECISION
        # =====================================

        if (
            class_match
            or
            field_match
        ):

            contact_forms.append(
                form
            )

    
    # =====================================
    # NO CONTACT FORM
    # =====================================

    if not contact_forms:

        print(
            "WARNING | Contact Form Detection |",
            "Forms exist, but no likely contact form was identified"
        )

        print(
            "\nContact Form Check Complete"
        )

        print(
            "---------------------------"
        )

        return

    print(
        "PASS | Contact Form Detection |",
        len(contact_forms),
        "likely contact form(s)"
    )

    # =====================================
    # ANALYZE EACH CONTACT FORM
    # =====================================

    for form_number, form in enumerate(
        contact_forms,
        start=1
    ):

        print(
            f"\nContact Form {form_number}"
        )

        # =====================================
        # FORM ID / CLASS
        # =====================================

        if form["id"]:

            print(
                "ID |",
                form["id"]
            )

        if form["className"]:

            print(
                "Class |",
                form["className"][:150]
            )

        # =====================================
        # VISIBILITY
        # =====================================

        if form["visible"]:

            print(
                "PASS | Form Visibility |",
                "Form is visible"
            )

        else:

            print(
                "INFO | Form Visibility |",
                "Form exists but is currently hidden"
            )

        # =====================================
        # METHOD
        # =====================================

        print(
            "INFO | Form Method |",
            form["method"]
        )

        # =====================================
        # ACTION
        # =====================================

        if form["action"]:

            print(
                "INFO | Form Action |",
                form["action"][:180]
            )

        else:

            print(
                "INFO | Form Action |",
                "No explicit action URL"
            )

        # =====================================
        # FIELDS
        # =====================================

        visible_fields = [
            field
            for field
            in form["fields"]
            if (
                field["visible"]
                and
                not field["disabled"]
                and
                field["type"]
                != "hidden"
            )
        ]

        print(
            "Fields |",
            len(visible_fields),
            "visible field(s)"
        )

        # =====================================
        # FIELD TYPE DETECTION
        # =====================================

        has_name = False
        has_email = False
        has_phone = False
        has_message = False

        unlabeled_fields = []

        required_count = 0

        for field in visible_fields:

            searchable = (
                field["name"]
                + " "
                + field["id"]
                + " "
                + field["placeholder"]
                + " "
                + field["label"]
                + " "
                + field["ariaLabel"]
            ).lower()

            field_type = (
                field["type"]
            )

            if (
                "name" in searchable
                and
                "username"
                not in searchable
            ):
                has_name = True

            if (
                field_type == "email"
                or
                "email" in searchable
                or
                "e-mail" in searchable
            ):
                has_email = True

            if (
                field_type == "tel"
                or
                "phone" in searchable
                or
                "mobile" in searchable
                or
                "telephone" in searchable
            ):
                has_phone = True

            if (
                field["tag"]
                == "textarea"
                or
                "message" in searchable
                or
                "comment" in searchable
                or
                "enquiry" in searchable
                or
                "inquiry" in searchable
            ):
                has_message = True

            if field["required"]:

                required_count += 1

            accessible_name = (
                field["label"]
                or
                field["ariaLabel"]
                or
                field["placeholder"]
            )

            if not accessible_name:

                unlabeled_fields.append(
                    field
                )

        # =====================================
        # NAME FIELD
        # =====================================

        if has_name:

            print(
                "PASS | Name Field |",
                "Detected"
            )

        else:

            print(
                "INFO | Name Field |",
                "Not detected"
            )

        # =====================================
        # EMAIL FIELD
        # =====================================

        if has_email:

            print(
                "PASS | Email Field |",
                "Detected"
            )

        else:

            print(
                "WARNING | Email Field |",
                "No email field detected"
            )

        # =====================================
        # PHONE FIELD
        # =====================================

        if has_phone:

            print(
                "PASS | Phone Field |",
                "Detected"
            )

        else:

            print(
                "INFO | Phone Field |",
                "Not detected"
            )

        # =====================================
        # MESSAGE FIELD
        # =====================================

        if has_message:

            print(
                "PASS | Message Field |",
                "Detected"
            )

        else:

            print(
                "INFO | Message Field |",
                "Not detected"
            )

        # =====================================
        # REQUIRED FIELDS
        # =====================================

        if required_count > 0:

            print(
                "PASS | Required Fields |",
                required_count,
                "required field(s)"
            )

        else:

            print(
                "WARNING | Required Fields |",
                "No required fields detected"
            )

        # =====================================
        # FIELD LABEL / ACCESSIBILITY CHECK
        # =====================================

        if unlabeled_fields:

            print(
                "WARNING | Field Labels |",
                len(unlabeled_fields),
                "field(s) have no label, aria-label or placeholder"
            )

            for field in (
                unlabeled_fields[:10]
            ):

                print(
                    "   ",
                    field["tag"].upper(),
                    "| type:",
                    field["type"],
                    "| name:",
                    field["name"]
                )

        else:

            print(
                "PASS | Field Labels |",
                "All visible fields have an accessible name"
            )

        # =====================================
        # SUBMIT BUTTON
        # =====================================

        visible_submit_buttons = [
            button
            for button
            in form[
                "submitButtons"
            ]
            if (
                button["visible"]
                and
                not button["disabled"]
            )
        ]

        if visible_submit_buttons:

            print(
                "PASS | Submit Button |",
                len(
                    visible_submit_buttons
                ),
                "visible submit button(s)"
            )

            for button in (
                visible_submit_buttons[:5]
            ):

                if button["text"]:

                    print(
                        "   Text |",
                        button["text"]
                    )

        else:

            print(
                "FAIL | Submit Button |",
                "No usable submit button detected"
            )

        # =====================================
        # CAPTCHA / ANTI-SPAM
        # =====================================

        if form[
            "captchaDetected"
        ]:

            print(
                "PASS | Anti-Spam |",
                "CAPTCHA or honeypot protection detected"
            )

        else:

            print(
                "INFO | Anti-Spam |",
                "No CAPTCHA/honeypot detected inside form"
            )

    # =====================================
    # IMPORTANT FUNCTIONAL NOTE
    # =====================================

    print(
        "\nINFO | Submission Test |",
        "Form was not submitted to avoid sending a real enquiry"
    )

    # =====================================
    # COMPLETE
    # =====================================

    print(
        "\nContact Form Check Complete"
    )

    print(
        "---------------------------"
    )